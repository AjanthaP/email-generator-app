"""Fault injection for the log-triage eval. Local only.

Each fault breaks the pipeline the way real systems break. The incident
generator (``scripts/triage/generate_incidents.py``) switches them on in
labelled time windows, and the triage agent has to work out which fault it
was from telemetry alone.

Safety:

- Off unless ``ENABLE_FAULTS=true``.
- Always off on Cloud Run (``K_SERVICE`` is set there), whatever
  ``ENABLE_FAULTS`` says.
- This module never logs, and its errors look like the real thing, so nothing
  in the telemetry names the injected fault.

Ways to switch faults on (only while enabled):

- ``FAULTS`` env var, for the whole process: ``FAULTS="quota_429:0.4"``
- ``X-Fault`` header on ``POST /api/email/generate``, for one request
- ``with faults.injected("slow_model:draft_writer:3"):`` in code

A spec is a comma-separated list of ``name[:arg[:arg]]``:

==============  ==============================  ==========================================
Fault           Args (defaults)                 Effect
==============  ==============================  ==========================================
quota_429       rate (1.0)                      each LLM call fails with a 429
                                                RESOURCE_EXHAUSTED error, with probability
                                                ``rate``; retries fail too
slow_model      agent (draft_writer), secs (3)  sleep before that agent's LLM calls
truncate        max_tokens (20)                 model output capped (finish MAX_TOKENS)
bad_prompt      factor (3)                      Review is asked for ``factor`` x the target
                                                length; prompt_version becomes v2
parser_garbage  -                               input parser gets non-JSON output
agent_crash     agent (tone_stylist)            that agent raises before doing any work
cost_spike      factor (5)                      every prompt gets ``factor`` x 1,500 chars
                                                of earlier-thread context (a context bug)
==============  ==============================  ==========================================
"""
from __future__ import annotations

import os
import random
import time
from contextlib import contextmanager, nullcontext
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, Optional, Tuple

from .config import settings

AGENTS = (
    "input_parser", "intent_detector", "draft_writer", "tone_stylist",
    "personalization", "review", "router",
)

# name -> (defaults, converters)
_SPECS: Dict[str, Tuple[tuple, tuple]] = {
    "quota_429": ((1.0,), (float,)),
    "slow_model": (("draft_writer", 3.0), (str, float)),
    "truncate": ((20,), (int,)),
    "bad_prompt": ((3.0,), (float,)),
    "parser_garbage": ((), ()),
    "agent_crash": (("tone_stylist",), (str,)),
    "cost_spike": ((5,), (int,)),
}
FAULT_NAMES = tuple(_SPECS)

BAD_PROMPT_VERSION = "v2"


class ResourceExhausted(Exception):
    """Same name and message shape as the Gemini API's quota error."""


_QUOTA_MESSAGE = (
    "429 RESOURCE_EXHAUSTED. You exceeded your current quota, please check your "
    "plan and billing details. For more information on this error, head to: "
    "https://ai.google.dev/gemini-api/docs/rate-limits. Please retry in 1s."
)
_CRASH_MESSAGE = "'NoneType' object has no attribute 'get'"
_GARBAGE = "Sure! Here is the information you asked for:\n\nRecipient - see above; purpose - follow up"

# Where cost_spike puts the extra context: the first of these params present.
_CONTEXT_PARAMS = ("reference_context", "context", "original_request", "user_input", "key_points", "draft")
_THREAD = (
    "Earlier in this thread: thanks for the update on the timeline. We reviewed the numbers "
    "with the team and agreed to revisit the open items next week. Please share any changes "
    "to the scope, the budget or the owners before then so we can plan accordingly. "
)


@dataclass(frozen=True)
class Fault:
    name: str
    args: tuple


@dataclass
class FaultSet:
    faults: Dict[str, Fault]
    rng: random.Random = field(default_factory=random.Random)

    def get(self, name: str) -> Optional[Fault]:
        return self.faults.get(name)


_active: ContextVar[Optional[FaultSet]] = ContextVar("faults_active", default=None)
_env_cache: Dict[str, FaultSet] = {}


def enabled() -> bool:
    return bool(getattr(settings, "enable_faults", False)) and not os.getenv("K_SERVICE")


def parse(spec: Optional[str]) -> Dict[str, Fault]:
    """Parse ``"quota_429:0.4,slow_model:review:2"``. Raises ValueError."""
    faults: Dict[str, Fault] = {}
    for part in (spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        name, *raw = part.split(":")
        name = name.strip().lower()
        if name not in _SPECS:
            raise ValueError(f"unknown fault {name!r}; choose from {', '.join(FAULT_NAMES)}")
        defaults, convert = _SPECS[name]
        if len(raw) > len(defaults):
            raise ValueError(f"too many arguments for {name}: {part!r}")
        args = list(defaults)
        for i, value in enumerate(raw):
            args[i] = convert[i](value.strip())
        if name in ("slow_model", "agent_crash") and args[0] not in AGENTS:
            raise ValueError(f"unknown agent {args[0]!r} in {part!r}")
        faults[name] = Fault(name, tuple(args))
    return faults


@contextmanager
def injected(spec: str, seed: Optional[int] = None) -> Iterator[FaultSet]:
    """Switch faults on for the current context. Raises if faults are disabled."""
    if not enabled():
        raise RuntimeError("faults are disabled: set ENABLE_FAULTS=true (never on Cloud Run)")
    fs = FaultSet(parse(spec), random.Random(seed))
    token = _active.set(fs)
    try:
        yield fs
    finally:
        _active.reset(token)


def from_header(value: Optional[str]):
    """Context manager for the X-Fault header; a no-op when disabled or empty."""
    if not value or not enabled():
        return nullcontext()
    try:
        return injected(value)
    except ValueError:
        return nullcontext()


def active() -> Optional[FaultSet]:
    if not enabled():
        return None
    fs = _active.get()
    if fs is not None:
        return fs
    spec = os.getenv("FAULTS") or getattr(settings, "faults", None)
    if not spec:
        return None
    if spec not in _env_cache:
        seed = os.getenv("FAULTS_SEED")
        _env_cache[spec] = FaultSet(parse(spec), random.Random(int(seed) if seed else None))
    return _env_cache[spec]


# ---- Hooks used by the app ---------------------------------------------------

def max_output_tokens() -> Optional[int]:
    """Output-token cap for new LLM clients (``truncate``)."""
    fs = active()
    fault = fs.get("truncate") if fs else None
    return int(fault.args[0]) if fault else None


def prompt_version() -> Optional[str]:
    """Prompt version to report for this request (``bad_prompt``)."""
    fs = active()
    return BAD_PROMPT_VERSION if fs and fs.get("bad_prompt") else None


def maybe_crash(agent: str) -> None:
    """Raise inside the pipeline before ``agent`` runs (``agent_crash``)."""
    fs = active()
    fault = fs.get("agent_crash") if fs else None
    if fault and fault.args[0] == agent:
        raise AttributeError(_CRASH_MESSAGE)


@dataclass
class CallPlan:
    """What the faults do to one LLM call. The no-op plan changes nothing."""

    params: dict
    quota_error: bool = False
    delay: float = 0.0
    garbage: bool = False

    def wrap(self, invoke: Callable[[dict], Any]) -> Callable[[dict], Any]:
        if not (self.quota_error or self.delay or self.garbage):
            return invoke

        def call(p: dict) -> Any:
            if self.delay:
                time.sleep(self.delay)
            if self.quota_error:
                raise ResourceExhausted(_QUOTA_MESSAGE)
            result = invoke(p)
            if self.garbage:
                result = _replace_content(result, _GARBAGE)
            return result

        return call


def plan_call(agent: str, params: dict) -> CallPlan:
    """Decide, once per LLM call, how the active faults change it."""
    fs = active()
    if fs is None:
        return CallPlan(params)
    plan = CallPlan(dict(params))

    fault = fs.get("quota_429")
    if fault and fs.rng.random() < float(fault.args[0]):
        plan.quota_error = True

    fault = fs.get("slow_model")
    if fault and fault.args[0] == agent:
        plan.delay = float(fault.args[1])

    if fs.get("parser_garbage") and agent == "input_parser":
        plan.garbage = True

    fault = fs.get("bad_prompt")
    if fault and agent == "review" and isinstance(plan.params.get("target_length"), (int, float)):
        plan.params["target_length"] = int(plan.params["target_length"] * float(fault.args[0]))

    fault = fs.get("cost_spike")
    if fault:
        key = next((k for k in _CONTEXT_PARAMS if isinstance(plan.params.get(k), str)), None)
        if key is not None:
            chars = max(1, int(fault.args[0])) * 1500
            block = (_THREAD * (chars // len(_THREAD) + 1))[:chars]
            plan.params[key] = f"{plan.params[key]}\n\n{block}"
    return plan


def _replace_content(result: Any, content: str) -> Any:
    if hasattr(result, "model_copy"):
        try:
            return result.model_copy(update={"content": content})
        except Exception:
            pass
    if isinstance(result, dict):
        return {**result, "content": content}
    return content


__all__ = [
    "FAULT_NAMES", "AGENTS", "BAD_PROMPT_VERSION", "Fault", "FaultSet", "CallPlan",
    "ResourceExhausted", "enabled", "parse", "injected", "from_header", "active",
    "max_output_tokens", "prompt_version", "maybe_crash", "plan_call",
]
