"""Structured telemetry for the email pipeline.

Every LLM call and every pipeline run produces one JSON event. Events go to:

- the ``telemetry`` logger, which ``src.utils.logging_config`` formats as one
  JSON line on stdout. Cloud Run forwards stdout to Cloud Logging, so these
  events can be queried there in production;
- an append-only JSONL file (``data/metrics/events-YYYY-MM-DD.jsonl`` by
  default). Local runs, the Day 2 incident generator and the Day 3 eval read
  these files.

``TELEMETRY_SINKS`` chooses the sinks: ``auto`` (default) means ``log`` on
Cloud Run, where the container filesystem lives in memory, and ``log,file``
everywhere else. Other values: ``log``, ``file``, ``log,file``, ``none``.

Event types (``schema`` 1):

- ``startup``: one per process start (revision, model, prompt version, flags)
- ``llm_call``: one per LLM invocation (fields of ``metrics.CallRecord``)
- ``agent_fallback``: an agent replaced model output with local fallback
  output, either because the call failed or because the output was unusable
- ``request_summary``: one per pipeline run, written when the run ends

Events never contain prompts, drafts or user IDs.
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
import threading
import time
import uuid
from collections import Counter
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

from .config import settings
from .prompts import PROMPT_VERSION

SCHEMA_VERSION = 1

logger = logging.getLogger("telemetry")
_file_lock = threading.Lock()

_QUOTA_MARKERS = ("quota", "429", "resourceexhausted", "resource_exhausted", "resource exhausted", "you exceeded", "generate_content_free_tier")
_TIMEOUT_MARKERS = ("timeout", "timed out", "deadline", "504")
_REQUEST_ID_RE = re.compile(r"[A-Za-z0-9._-]{8,64}")


@dataclass
class RequestContext:
    """Per-request telemetry state, held in a contextvar for the run's thread."""

    request_id: str
    endpoint: str
    prompt_version: str = PROMPT_VERSION
    started_perf: float = field(default_factory=time.perf_counter)
    calls: List[Dict[str, Any]] = field(default_factory=list)
    fallbacks: List[Dict[str, str]] = field(default_factory=list)


_request: ContextVar[Optional[RequestContext]] = ContextVar("telemetry_request", default=None)
_agent: ContextVar[Optional[str]] = ContextVar("telemetry_agent", default=None)


# ---- Request and agent context -------------------------------------------

def new_request_id() -> str:
    return uuid.uuid4().hex[:16]


def request_id_from_header(value: Optional[str]) -> str:
    """Reuse a caller-supplied X-Request-ID if it looks safe, else make one."""
    if value and _REQUEST_ID_RE.fullmatch(value.strip()):
        return value.strip()
    return new_request_id()


@contextmanager
def request_scope(
    endpoint: str, request_id: Optional[str] = None, prompt_version: Optional[str] = None
) -> Iterator[RequestContext]:
    """Bind a request context for the duration of a pipeline run.

    Set this inside the thread that runs the work: the workflow runs through
    ``run_in_threadpool``, so the request handler's own context is not where
    the agents execute. ``prompt_version`` overrides ``PROMPT_VERSION``.
    """
    ctx = RequestContext(
        request_id=request_id or new_request_id(),
        endpoint=endpoint,
        prompt_version=prompt_version or PROMPT_VERSION,
    )
    token = _request.set(ctx)
    try:
        yield ctx
    finally:
        _request.reset(token)


@contextmanager
def agent_scope(agent: str) -> Iterator[None]:
    token = _agent.set(agent)
    try:
        yield
    finally:
        _agent.reset(token)


def current_request() -> Optional[RequestContext]:
    return _request.get()


def current_request_id() -> Optional[str]:
    ctx = _request.get()
    return ctx.request_id if ctx else None


def current_agent() -> Optional[str]:
    return _agent.get()


def current_prompt_version() -> str:
    ctx = _request.get()
    return ctx.prompt_version if ctx else PROMPT_VERSION


def classify_error(error: Any) -> Optional[str]:
    """Map an exception or message to ``quota``, ``timeout`` or ``error``."""
    if error is None:
        return None
    if isinstance(error, BaseException):
        text = f"{type(error).__name__}: {error}"
    else:
        text = str(error)
    text = text.lower()
    if any(m in text for m in _QUOTA_MARKERS):
        return "quota"
    if any(m in text for m in _TIMEOUT_MARKERS):
        return "timeout"
    return "error"


# ---- Sinks ------------------------------------------------------------------

def active_sinks() -> set:
    raw = str(getattr(settings, "telemetry_sinks", "auto") or "auto").strip().lower()
    if raw == "auto":
        return {"log"} if os.getenv("K_SERVICE") else {"log", "file"}
    if raw in ("none", "off", "false", "0"):
        return set()
    return {part.strip() for part in raw.split(",") if part.strip()}


def telemetry_file_path() -> str:
    explicit = getattr(settings, "telemetry_file", None)
    if explicit:
        return explicit
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return os.path.join(settings.metrics_output_dir, f"events-{day}.jsonl")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _write_file(event: Dict[str, Any]) -> None:
    path = telemetry_file_path()
    line = json.dumps(event, default=str, ensure_ascii=False)
    with _file_lock:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def emit(event_type: str, message: str = "", level: int = logging.INFO, **fields: Any) -> Dict[str, Any]:
    """Write one telemetry event to the active sinks. Never raises."""
    event: Dict[str, Any] = {
        "event": event_type,
        "schema": SCHEMA_VERSION,
        "ts": _iso_now(),
        "service": os.getenv("K_SERVICE", "email-generator-app"),
        "revision": os.getenv("K_REVISION", "local"),
    }
    ctx = _request.get()
    if ctx is not None:
        event["request_id"] = ctx.request_id
        event["endpoint"] = ctx.endpoint
    event.update(fields)
    try:
        sinks = active_sinks()
        if "file" in sinks:
            _write_file(event)
        if "log" in sinks:
            logger.log(level, message or event_type, extra={"json_fields": event})
    except Exception:  # pragma: no cover - telemetry must never break a request
        try:
            sys.stderr.write("telemetry emit failed\n")
        except Exception:
            pass
    return event


# ---- Event helpers -----------------------------------------------------------

def record_llm_call(record: Any) -> Dict[str, Any]:
    """Emit an ``llm_call`` event for a ``metrics.CallRecord``."""
    data = asdict(record)
    data.pop("timestamp", None)
    ctx = _request.get()
    if ctx is not None:
        ctx.calls.append(data)
    level = logging.WARNING if data.get("error") else logging.INFO
    msg = (
        f"llm_call agent={data.get('agent')} latency_ms={data.get('latency_ms', 0):.0f} "
        f"finish={data.get('finish_reason')} retries={data.get('retries')} error_type={data.get('error_type')}"
    )
    return emit("llm_call", msg, level=level, **data)


def record_fallback(reason: str, agent: Optional[str] = None, detail: Optional[str] = None) -> Dict[str, Any]:
    """Record that an agent used local fallback output instead of the model's.

    ``reason`` is ``quota``, ``timeout``, ``error`` (from ``classify_error``) or
    ``invalid_output`` when the call succeeded but its output was unusable.
    """
    name = agent or _agent.get() or "unknown"
    ctx = _request.get()
    if ctx is not None:
        ctx.fallbacks.append({"agent": name, "reason": reason})
    return emit(
        "agent_fallback",
        f"agent {name} used local fallback ({reason})",
        level=logging.WARNING,
        agent=name,
        reason=reason,
        detail=(detail or "")[:300],
        prompt_version=current_prompt_version(),
    )


def _final_text(state: Dict[str, Any]) -> str:
    for key in ("final_draft", "personalized_draft", "styled_draft", "draft"):
        value = state.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def emit_request_summary(
    state: Optional[Dict[str, Any]],
    *,
    status: str,
    agents_run: Optional[List[str]] = None,
    agents_skipped: Optional[List[str]] = None,
    stub_reason: Optional[str] = None,
    error: Optional[BaseException] = None,
) -> Optional[Dict[str, Any]]:
    """Emit the ``request_summary`` event for the current request context."""
    ctx = _request.get()
    if ctx is None:
        return None
    state = state or {}
    md = state.get("metadata") or {}
    calls = ctx.calls
    review_notes = state.get("review_notes") or {}

    if agents_run is None:
        agents_run = list(dict.fromkeys(c.get("agent") for c in calls if c.get("agent")))
    agents_errored = sorted(
        k for k, v in review_notes.items()
        if k != "gemini_quota_fallback" and isinstance(v, dict) and "error" in v
    )
    fallback_agents = sorted({f["agent"] for f in ctx.fallbacks})

    final_words = len(_final_text(state).split())
    target = state.get("length_preference") or md.get("effective_length_preference") or md.get("requested_length_preference")
    try:
        target = int(target) if target else None
    except (TypeError, ValueError):
        target = None
    # Deviation uses the pre-trim count: trimming would otherwise hide a prompt
    # that makes the model write far too much.
    words_before_trim = md.get("original_word_count", final_words)
    deviation = round((words_before_trim - target) / target * 100.0, 1) if target else None

    source = md.get("source", "llm")
    is_fallback = stub_reason == "quota_fallback" or bool(fallback_agents)
    llm_errors = sum(1 for c in calls if c.get("error"))
    finish_reasons = Counter(c.get("finish_reason") for c in calls if c.get("finish_reason"))
    error_types = Counter(c.get("error_type") for c in calls if c.get("error_type"))

    fields = {
        "status": status,
        "source": source,
        "stub_reason": stub_reason,
        "is_fallback": is_fallback,
        "model": md.get("model") or md.get("fallback_from_model"),
        "prompt_version": ctx.prompt_version,
        "intent": state.get("intent"),
        "tone": state.get("tone"),
        "agents_run": agents_run,
        "agents_skipped": agents_skipped or [],
        "agents_errored": agents_errored,
        "fallback_agents": fallback_agents,
        "llm_calls": len(calls),
        "llm_errors": llm_errors,
        "error_types": dict(error_types),
        "retries": sum(int(c.get("retries") or 0) for c in calls),
        "finish_reasons": dict(finish_reasons),
        "truncated_calls": finish_reasons.get("MAX_TOKENS", 0),
        "tokens_in": sum(int(c.get("input_tokens") or 0) for c in calls),
        "tokens_out": sum(int(c.get("output_tokens") or 0) for c in calls),
        "cost_usd": round(sum(float(c.get("cost_usd") or 0.0) for c in calls), 8),
        "llm_latency_ms": round(sum(float(c.get("latency_ms") or 0.0) for c in calls), 1),
        "latency_ms": round((time.perf_counter() - ctx.started_perf) * 1000.0, 1),
        "target_words": target,
        "words_before_trim": words_before_trim,
        "final_words": final_words,
        "length_deviation_pct": deviation,
        "length_trimmed": bool(md.get("length_trimmed", False)),
        "error": (f"{type(error).__name__}: {error}"[:300] if error else None),
    }
    degraded = status != "ok" or is_fallback or llm_errors > 0
    msg = (
        f"request {ctx.request_id} {status} source={source} calls={len(calls)} "
        f"errors={llm_errors} fallbacks={len(fallback_agents)} latency_ms={fields['latency_ms']:.0f}"
    )
    return emit("request_summary", msg, level=logging.WARNING if degraded else logging.INFO, **fields)


def emit_startup(**overrides: Any) -> Dict[str, Any]:
    """Emit a ``startup`` event so deploys and config changes appear in the timeline.

    ``overrides`` replace reported fields (the incident generator uses this to
    record simulated deploys).
    """
    fields: Dict[str, Any] = {
        "model": settings.gemini_model,
        "prompt_version": PROMPT_VERSION,
        "max_tokens": settings.max_tokens,
        "temperature": settings.temperature,
        "llm_router": bool(settings.enable_llm_router),
        "database": bool(getattr(settings, "database_url", None)),
        "telemetry_sinks": sorted(active_sinks()),
        "python": sys.version.split()[0],
    }
    fields.update(overrides)
    return emit(
        "startup",
        f"startup model={fields['model']} prompt_version={fields['prompt_version']}",
        **fields,
    )


__all__ = [
    "RequestContext", "SCHEMA_VERSION", "new_request_id", "request_id_from_header",
    "request_scope", "agent_scope", "current_request", "current_request_id",
    "current_agent", "current_prompt_version", "classify_error", "active_sinks",
    "telemetry_file_path", "emit", "record_llm_call", "record_fallback",
    "emit_request_summary", "emit_startup",
]
