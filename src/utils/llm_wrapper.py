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
from typing import Any, Callable, Optional

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

        # Wrap bound method call
        bound = chain.invoke
        return self.run_with_retries(bound, params, **retry_kwargs)


# Simple module-level factory for convenience
def make_wrapper(llm: Any, **kwargs) -> LLMWrapper:
    """Factory helper to create an LLMWrapper quickly."""
    return LLMWrapper(llm, **kwargs)
