"""A scripted stand-in for Gemini, for generating incidents offline.

It reads the same prompts the real model gets and answers in the shape each
agent expects: JSON for the input parser, an intent name, the Router's JSON,
and, for the writing agents, an email of the requested length ("Target
Length: N words"). Token counts come from the actual prompt and reply text,
replies are cut at ``max_output_tokens`` with ``finish_reason=MAX_TOKENS``,
and each call takes a little time. So length, cost, truncation and latency
faults show up in telemetry the way they would with Gemini.

It reports the production model name, because telemetry must not reveal
that the run was scripted.
"""
from __future__ import annotations

import json
import random
import re
import time
from typing import Any, List, Optional, Tuple

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import PrivateAttr

_TARGET = re.compile(r"target length:[^\d\n]{0,40}(\d+)\s*words", re.IGNORECASE)
_RECIPIENT = re.compile(r"^\s*recipient:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
_GREETING = re.compile(r"\b(?:Dear|Hi|Hello)\s+([^,\n]{1,60}),")
_SECTION = re.compile(r"(?:User Request|Original User Request):\s*(.*?)(?:\n\s*\n\s*[A-Z][^\n]{0,40}:|\Z)", re.DOTALL)

_FILLER = (
    "Thank you for your time and the helpful conversation earlier this week. I wanted to "
    "follow up on the points we discussed, share a short update on where things stand, and "
    "confirm the next steps so that we stay aligned. The team has made steady progress and "
    "we expect to close the remaining items soon. Please let me know if anything should "
    "change, or if you would like more detail on any part of this before we continue."
).split()

_INTENTS = [
    ("leave", "leave_request"), ("time off", "leave_request"), ("follow", "follow_up"),
    ("thank", "thank_you"), ("meeting", "meeting_request"), ("schedule", "meeting_request"),
    ("apolog", "apology"), ("status", "status_update"), ("introduc", "introduction"),
    ("documentation", "information_request"), ("ask for", "information_request"),
    ("complain", "complaint"),
]


def _tokens(text: str) -> int:
    return max(1, len(text) // 4)


class ScriptedGemini(BaseChatModel):
    """Fake chat model that answers each agent's prompt plausibly."""

    model: str = "gemini-3.5-flash-lite"
    max_output_tokens: int = 1000
    latency_ms: Tuple[float, float] = (40.0, 160.0)
    seed: Optional[int] = None
    _rng: Any = PrivateAttr(default=None)

    @property
    def _llm_type(self) -> str:
        return "scripted-gemini"

    def _random(self) -> random.Random:
        if self._rng is None:
            self._rng = random.Random(self.seed)
        return self._rng

    def _generate(
        self, messages: List[BaseMessage], stop: Optional[List[str]] = None, run_manager: Any = None, **kwargs: Any
    ) -> ChatResult:
        rng = self._random()
        prompt = "\n".join(str(getattr(m, "content", m)) for m in messages)
        low = prompt.lower()
        time.sleep(rng.uniform(*self.latency_ms) / 1000.0)

        if "extract the following information" in low:
            content = self._parse(prompt)
        elif "classifying email intents" in low:
            content = self._intent(prompt)
        elif "workflow controller" in low:
            content = json.dumps({"decision": "continue", "reason": "Draft is acceptable."})
        else:
            content = self._email(prompt, rng)

        out_tokens = _tokens(content)
        finish = "STOP"
        if out_tokens > self.max_output_tokens:
            content = content[: self.max_output_tokens * 4]
            out_tokens = self.max_output_tokens
            finish = "MAX_TOKENS"
        in_tokens = _tokens(prompt)
        message = AIMessage(
            content=content,
            response_metadata={"finish_reason": finish, "model_name": self.model},
            usage_metadata={"input_tokens": in_tokens, "output_tokens": out_tokens, "total_tokens": in_tokens + out_tokens},
        )
        return ChatResult(generations=[ChatGeneration(message=message)])

    # ---- Replies per agent ---------------------------------------------------

    @staticmethod
    def _request(prompt: str) -> str:
        match = _SECTION.search(prompt)
        return (match.group(1) if match else prompt).strip()

    def _parse(self, prompt: str) -> str:
        request = self._request(prompt)
        recipient = _RECIPIENT.search(request)
        body = [ln.strip() for ln in request.splitlines() if ln.strip() and ":" not in ln[:20]]
        text = " ".join(body) or request
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        data = {
            "recipient_name": recipient.group(1) if recipient else "Recipient",
            "recipient_email": "",
            "email_purpose": sentences[0] if sentences else text[:120],
            "key_points": sentences[:3] or [text[:100]],
            "tone_preference": "formal",
            "constraints": {},
            "context": text[:200],
        }
        return "```json\n" + json.dumps(data, indent=2) + "\n```"

    def _intent(self, prompt: str) -> str:
        request = self._request(prompt).lower()
        for keyword, intent in _INTENTS:
            if keyword in request:
                return intent
        return "generic"

    def _email(self, prompt: str, rng: random.Random) -> str:
        match = _TARGET.search(prompt)
        target = int(match.group(1)) if match else 120
        greeting = _GREETING.search(prompt)
        recipient = _RECIPIENT.search(prompt)
        name = (greeting.group(1) if greeting else recipient.group(1) if recipient else "there").strip()
        # The model lands within a few percent of the target, as Gemini usually does.
        words = max(10, int(target * rng.uniform(0.94, 1.03)))
        body_words = max(4, words - 4)  # "Dear X," and "Best regards" count too
        body = " ".join(_FILLER[i % len(_FILLER)] for i in range(body_words))
        return f"Dear {name},\n\n{body}\n\nBest regards"


__all__ = ["ScriptedGemini"]
