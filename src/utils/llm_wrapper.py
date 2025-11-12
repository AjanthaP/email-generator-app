"""
Lightweight LLM wrapper to centralize retry/backoff and server-suggested retry handling.

Usage pattern:

from src.utils.llm_wrapper import LLMWrapper
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model=..., google_api_key=...)
wrapper = LLMWrapper(llm)

# Wrap arbitrary LLM call (callable) with retries:
response = wrapper.run_with_retries(chain.invoke, {"user_input": "..."})

# Convenience for prompt chains:
response = wrapper.invoke_chain(chain, {"user_input": "..."})

The wrapper is intentionally synchronous and minimal. It provides:
- exponential backoff
- honoring server-suggested retry delays when discoverable
- configurable retry limits and backoff factor
- structured error propagation

This module is safe to import into agents and the workflow. Agents should adopt
`wrapper.invoke_chain(chain, params)` instead of calling `chain.invoke(params)` directly.
"""

from __future__ import annotations

import re
import time
import logging
from typing import Any, Callable, Optional, Tuple

from .config import settings
from .metrics import metrics
try:
    # Optional: rate limiter is only used when enabled
    from .rate_limiter import RateLimiter
except Exception:  # pragma: no cover - defensive import
    RateLimiter = None  # type: ignore

logger = logging.getLogger(__name__)


class LLMWrapperError(Exception):
    """Generic wrapper-level exception."""


class LLMWrapper:
    def __init__(
        self,
        llm: Any,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        backoff_factor: float = 2.0,
        max_backoff: float = 60.0,
    ) -> None:
        """Create an LLM wrapper.

        Args:
            llm: The underlying LLM client instance (e.g., ChatGoogleGenerativeAI).
            max_retries: Number of retry attempts for transient errors (excludes initial try).
            initial_backoff: Starting backoff in seconds.
            backoff_factor: Multiplicative factor for exponential backoff.
            max_backoff: Maximum backoff in seconds.
        """
        self.llm = llm
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.backoff_factor = backoff_factor
        self.max_backoff = max_backoff
        # Initialize a rate limiter if feature is enabled and implementation is available
        self._rate_limiter = None
        if getattr(settings, "enable_rate_limiter", False) and RateLimiter is not None:
            try:
                self._rate_limiter = RateLimiter(
                    rpm=settings.requests_per_minute,
                    tpm=settings.tokens_per_minute,
                    max_concurrency=settings.max_concurrency,
                    jitter_ms=settings.rate_limiter_jitter_ms,
                )
            except Exception:
                logger.exception("Failed to initialize RateLimiter; proceeding without client-side limits.")
                self._rate_limiter = None

    def _parse_retry_delay(self, exc: Exception) -> Optional[float]:
        """Try to parse a server-suggested retry delay from the exception message.

        Heuristics:
        - Look for 'retry in Xs' or 'Please retry in Xs' where X is seconds.
        - Look for 'retry_delay.*seconds: N' style (protobuf-like stringification).
        - Look for 'retry-after: N' or 'retry-after=N'.

        Returns seconds as float if found, else None.
        """
        try:
            text = str(exc)
        except Exception:
            return None

        if not text:
            return None

        # Common patterns
        patterns = [
            r"retry in\s*(\d+(?:\.\d+)?)s",
            r"please retry in\s*(\d+(?:\.\d+)?)s",
            r"retry_after[:=]\s*(\d+(?:\.\d+)?)",
            r"retry-after[:=]\s*(\d+(?:\.\d+)?)",
            r"seconds:\s*(\d+(?:\.\d+)?)",
        ]

        for pat in patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                try:
                    return float(m.group(1))
                except Exception:
                    continue

        # Last resort: look for a number following 'retry' within 30 chars
        m = re.search(r"retry[^\d\n\r]{0,30}(\d+(?:\.\d+)?)", text, flags=re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                pass

        return None

    def run_with_retries(
        self,
        func: Callable[..., Any],
        *args,
        max_retries: Optional[int] = None,
        initial_backoff: Optional[float] = None,
        backoff_factor: Optional[float] = None,
        max_backoff: Optional[float] = None,
        **kwargs,
    ) -> Any:
        """Run a callable that performs an LLM call with retries/backoff.

        The callable is expected to raise exceptions for failures. This wrapper
        will retry transient failures and honor server-suggested retry delays if
        they can be parsed from the exception text.

        Args:
            func: Callable to execute (e.g., chain.invoke)
            *args/**kwargs: Passed to the callable.
            max_retries, initial_backoff, backoff_factor, max_backoff: optional
                overrides for retry policy.

        Returns:
            The result of `func(*args, **kwargs)` on success.

        Raises:
            LLMWrapperError: if all retries are exhausted or a non-retriable
                error occurs.
        """
        mr = self.max_retries if max_retries is None else max_retries
        ib = self.initial_backoff if initial_backoff is None else initial_backoff
        bf = self.backoff_factor if backoff_factor is None else backoff_factor
        mb = self.max_backoff if max_backoff is None else max_backoff

        attempt = 0
        while True:
            try:
                attempt += 1
                return func(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - we want to catch all and rethrow
                # Parse retry delay if server suggested one
                suggested = self._parse_retry_delay(exc)

                # If we've exhausted attempts, raise a wrapper error with context
                if attempt > mr:
                    logger.exception("LLM call failed after %d attempts", attempt)
                    raise LLMWrapperError(f"LLM call failed after {attempt} attempts: {exc}") from exc

                # Decide how long to wait: prefer server-suggested, else exponential
                if suggested is not None and suggested > 0:
                    delay = min(suggested, mb)
                    logger.warning(
                        "LLM server suggested retry delay: %s seconds (using as wait)", delay
                    )
                else:
                    # exponential backoff
                    delay = min(ib * (bf ** (attempt - 1)), mb)
                    logger.info("LLM call failed (attempt %d/%d). Backing off for %.1fs", attempt, mr, delay)

                # Small safety: if delay is large, cap it
                if delay > mb:
                    delay = mb

                time.sleep(delay)
                # loop and retry

    def invoke_chain(self, chain: Any, params: dict, **retry_kwargs) -> Any:
        """Convenience wrapper for LangChain prompt chains that expose `invoke`.

        `chain` is expected to be a callable object with an `invoke(params)` method
        (for example, the result of `prompt | llm`).

        Returns the chain's response object (whatever the underlying library returns).
        """
        if not hasattr(chain, "invoke"):
            raise ValueError("Provided chain does not have an 'invoke' method")

        # Token estimate for rate limiter pre-check (best-effort)
        est_in_tokens = self._estimate_input_tokens(params)

        # Apply client-side rate limiting if configured
        if self._rate_limiter is not None:
            self._rate_limiter.acquire(est_in_tokens)

        # Wrap bound method call
        bound = chain.invoke

        start = time.time()
        error_msg: Optional[str] = None
        try:
            result = self.run_with_retries(bound, params, **retry_kwargs)
            return result
        except Exception as exc:
            error_msg = str(exc)
            raise
        finally:
            # Always attempt to record metrics after the call (success or error)
            latency_ms = (time.time() - start) * 1000.0
            try:
                if hasattr(chain, "_lc_kwargs") and isinstance(chain._lc_kwargs, dict):  # type: ignore[attr-defined]
                    model_name = getattr(self.llm, "model", None) or chain._lc_kwargs.get("model") or "unknown"
                else:
                    model_name = getattr(self.llm, "model", None) or "unknown"

                in_tok, out_tok = self._extract_token_usage(result if 'result' in locals() else None)
                # Fallback to estimates when usage not available
                if in_tok is None:
                    in_tok = est_in_tokens
                if out_tok is None:
                    out_tok = self._estimate_output_tokens(result) if 'result' in locals() else 0

                cost = 0.0
                if getattr(settings, "enable_cost_tracking", False):
                    cost = metrics.compute_cost(model_name, in_tok, out_tok)

                metrics.record_call(
                    model=model_name,
                    latency_ms=latency_ms,
                    input_tokens=int(in_tok or 0),
                    output_tokens=int(out_tok or 0),
                    cost_usd=float(cost or 0.0),
                    error=error_msg,
                )
            except Exception:
                # Never fail user flow due to metrics
                logger.debug("Metrics recording failed", exc_info=True)
            finally:
                # Release concurrency slot if limiter is in use
                try:
                    if self._rate_limiter is not None:
                        self._rate_limiter.release()
                except Exception:
                    pass

    # ---- Helpers ----
    def _estimate_input_tokens(self, params: dict) -> int:
        try:
            if not params:
                return 0
            # Rough heuristic: 1 token ~ 4 chars for English
            text = " ".join(
                [str(v) for v in params.values() if isinstance(v, (str, int, float))]
            )
            return max(1, int(len(text) / 4))
        except Exception:
            return 0

    def _estimate_output_tokens(self, result: Any) -> int:
        try:
            content = None
            if result is None:
                return 0
            if hasattr(result, "content"):
                content = result.content
            elif isinstance(result, dict) and "content" in result:
                content = result.get("content")
            if content is None:
                return 0
            return max(1, int(len(str(content)) / 4))
        except Exception:
            return 0

    def _extract_token_usage(self, result: Any) -> Tuple[Optional[int], Optional[int]]:
        """Try to extract token usage from common LangChain/LLM message shapes.

        Returns a tuple (input_tokens, output_tokens), values may be None if not available.
        """
        in_tok = out_tok = None
        try:
            # Debug: log what we're working with
            if getattr(settings, "debug", False):
                logger.debug("Attempting token extraction from result type: %s", type(result).__name__)
            
            # LangChain AIMessage often carries response_metadata
            meta = getattr(result, "response_metadata", None)
            if isinstance(meta, dict):
                if getattr(settings, "debug", False):
                    logger.debug("Found response_metadata: %s", list(meta.keys()))
                # Check direct fields
                in_tok = meta.get("input_tokens") or meta.get("prompt_token_count")
                out_tok = meta.get("output_tokens") or meta.get("candidates_token_count")

            # Some providers put usage under additional_kwargs["usage_metadata"]
            if in_tok is None or out_tok is None:
                add = getattr(result, "additional_kwargs", None)
                if isinstance(add, dict):
                    if getattr(settings, "debug", False):
                        logger.debug("Found additional_kwargs: %s", list(add.keys()))
                    usage = add.get("usage_metadata") or add.get("token_usage")
                    if isinstance(usage, dict):
                        if getattr(settings, "debug", False):
                            logger.debug("Found usage dict: %s", usage)
                        in_tok = in_tok or usage.get("input_tokens") or usage.get("prompt_tokens")
                        out_tok = out_tok or usage.get("output_tokens") or usage.get("completion_tokens")

            # Google Generative AI SDK sometimes returns usage inside result.usage_metadata
            if in_tok is None or out_tok is None:
                usage_meta = getattr(result, "usage_metadata", None)
                if isinstance(usage_meta, dict):
                    if getattr(settings, "debug", False):
                        logger.debug("Found usage_metadata at top level: %s", usage_meta)
                    in_tok = in_tok or usage_meta.get("prompt_token_count") or usage_meta.get("input_tokens")
                    out_tok = out_tok or usage_meta.get("candidates_token_count") or usage_meta.get("output_tokens")
            
            if getattr(settings, "debug", False) and (in_tok or out_tok):
                logger.debug("Extracted tokens: in=%s, out=%s", in_tok, out_tok)
        except Exception:
            logger.debug("Token extraction failed", exc_info=True)
            return None, None

        # Normalize to ints if possible
        try:
            if in_tok is not None:
                in_tok = int(in_tok)
            if out_tok is not None:
                out_tok = int(out_tok)
        except Exception:
            pass

        return in_tok, out_tok


# Simple module-level factory for convenience
def make_wrapper(llm: Any, **kwargs) -> LLMWrapper:
    """Factory helper to create an LLMWrapper quickly."""
    return LLMWrapper(llm, **kwargs)
