"""Day 1 telemetry: one request ID per run, one event per LLM call, one summary."""
import json
import logging
from typing import Any, Dict, List, Optional

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from src.utils import telemetry
from src.utils.config import settings
from src.utils.llm_wrapper import LLMWrapper
from src.utils.logging_config import JsonFormatter
from src.workflow.pipeline import default_graph_order, execute_workflow

PROMPT = "Recipient: Sarah\n\nFollow up with Sarah about the proposal we sent last week and ask for feedback."
DRAFT = "Dear Sarah,\n\n" + " ".join(["I wanted to follow up on the proposal we shared last week."] * 5) + "\n\nBest regards"


class ScriptedChat(BaseChatModel):
    """Fake Gemini that answers by agent, using the pipeline's agent scope."""

    model: str = "fake-gemini"
    fail: Dict[str, str] = {}
    garbage: List[str] = []
    finish_reason: str = "STOP"

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        agent = telemetry.current_agent()
        if agent in self.fail:
            raise RuntimeError(self.fail[agent])
        if agent in self.garbage:
            content = "this is not json"
        elif agent == "input_parser":
            content = json.dumps({
                "recipient_name": "Sarah",
                "email_purpose": "Follow up on the proposal",
                "key_points": ["proposal sent last week", "ask for feedback"],
                "tone_preference": "formal",
                "constraints": {},
                "context": "follow up",
            })
        elif agent == "intent_detector":
            content = "follow_up"
        elif agent == "router":
            content = '{"decision": "continue", "reason": "looks fine"}'
        else:
            content = DRAFT
        msg = AIMessage(
            content=content,
            response_metadata={"finish_reason": self.finish_reason},
            usage_metadata={"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
        )
        return ChatResult(generations=[ChatGeneration(message=msg)])


@pytest.fixture
def events_file(tmp_path, monkeypatch):
    path = tmp_path / "events.jsonl"
    monkeypatch.setattr(settings, "telemetry_sinks", "file")
    monkeypatch.setattr(settings, "telemetry_file", str(path))
    monkeypatch.setattr(settings, "enable_llm_router", True)
    monkeypatch.setattr(settings, "enable_chromadb", False, raising=False)
    monkeypatch.setattr("src.utils.llm_wrapper.time.sleep", lambda s: None)
    return path


def read_events(path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def of_type(events, kind) -> List[Dict[str, Any]]:
    return [e for e in events if e["event"] == kind]


def run(llm, request_id="test-req-0001", **kwargs):
    return execute_workflow(
        PROMPT, llm=llm, use_stub=False, length_preference=60,
        request_id=request_id, endpoint="test", **kwargs,
    )


def test_one_request_id_per_run_with_call_rows_and_summary(events_file):
    state = run(ScriptedChat())
    events = read_events(events_file)
    calls = of_type(events, "llm_call")
    summaries = of_type(events, "request_summary")

    assert [c["agent"] for c in calls] == default_graph_order()
    assert {e["request_id"] for e in events} == {"test-req-0001"}
    assert all(c["prompt_version"] == "v1" and c["finish_reason"] == "STOP" for c in calls)
    assert all(c["retries"] == 0 and c["error"] is None for c in calls)
    assert all(c["cost_usd"] > 0 for c in calls), "cost is always estimated for telemetry"

    assert len(summaries) == 1
    s = summaries[0]
    assert s["status"] == "ok" and s["source"] == "llm" and s["is_fallback"] is False
    assert s["llm_calls"] == 7 and s["llm_errors"] == 0
    assert s["tokens_in"] == 700 and s["tokens_out"] == 350
    assert s["finish_reasons"] == {"STOP": 7}
    assert s["target_words"] == 60 and s["length_deviation_pct"] is not None
    assert s["agents_run"] == default_graph_order()
    assert s["model"] == "gemini-2.0-flash-lite", "review/router metadata must not wipe the pipeline's"
    assert state["metadata"]["request_id"] == "test-req-0001"
    assert state["metadata"]["llm_router_used"] is True
    assert of_type(events, "agent_fallback") == []


def test_router_prompt_formats():
    from src.utils.prompts import ROUTER_AGENT_PROMPT
    text = ROUTER_AGENT_PROMPT.format(state_summary="error=None")
    assert '{"decision": "continue|retry|fallback"' in text


def test_quota_mid_request_is_silent_to_user_but_visible_in_telemetry(events_file):
    llm = ScriptedChat(fail={"tone_stylist": "429 ResourceExhausted: You exceeded your current quota"})
    state = run(llm)
    events = read_events(events_file)

    # What the user sees: a normal LLM response.
    assert state["metadata"]["source"] == "llm"
    assert state.get("final_draft")

    # What telemetry sees.
    failed = [c for c in of_type(events, "llm_call") if c["error"]]
    assert len(failed) == 1 and failed[0]["agent"] == "tone_stylist"
    assert failed[0]["error_type"] == "quota" and failed[0]["retries"] == 3
    fallbacks = of_type(events, "agent_fallback")
    assert [(f["agent"], f["reason"]) for f in fallbacks] == [("tone_stylist", "quota")]
    s = of_type(events, "request_summary")[0]
    assert s["is_fallback"] is True and s["fallback_agents"] == ["tone_stylist"]
    assert s["llm_errors"] == 1 and s["error_types"] == {"quota": 1} and s["retries"] == 3


def test_quota_at_parser_falls_back_to_stub(events_file):
    llm = ScriptedChat(fail={"input_parser": "429 ResourceExhausted: quota"})
    state = run(llm)
    s = of_type(read_events(events_file), "request_summary")[0]

    assert state["metadata"]["source"] == "stub"
    assert s["source"] == "stub" and s["stub_reason"] == "quota_fallback"
    assert s["agents_run"] == ["input_parser"]
    assert s["agents_skipped"] == default_graph_order()[1:]
    assert s["agents_errored"] == ["input_parser"]


def test_parser_garbage_is_a_fallback_without_an_llm_error(events_file):
    run(ScriptedChat(garbage=["input_parser"]))
    events = read_events(events_file)
    parser_call = [c for c in of_type(events, "llm_call") if c["agent"] == "input_parser"][0]
    assert parser_call["error"] is None
    assert [(f["agent"], f["reason"]) for f in of_type(events, "agent_fallback")] == [("input_parser", "invalid_output")]


def test_truncated_outputs_are_counted(events_file):
    run(ScriptedChat(finish_reason="MAX_TOKENS"))
    s = of_type(read_events(events_file), "request_summary")[0]
    assert s["truncated_calls"] == 7


def test_requested_stub_has_no_calls(events_file):
    execute_workflow(PROMPT, use_stub=True, request_id="test-req-stub1", endpoint="test")
    events = read_events(events_file)
    assert of_type(events, "llm_call") == []
    s = of_type(events, "request_summary")[0]
    assert s["source"] == "stub" and s["stub_reason"] == "requested" and s["is_fallback"] is False


def test_wrapper_records_retries(events_file):
    class Flaky:
        def __init__(self):
            self.n = 0

        def invoke(self, params):
            self.n += 1
            if self.n < 3:
                raise RuntimeError("temporary failure")
            return AIMessage(content="ok")

    wrapper = LLMWrapper(llm=None, max_retries=3, initial_backoff=0.0)
    with telemetry.request_scope("test", "test-req-retry"):
        wrapper.invoke_chain(Flaky(), {"x": "y"}, agent="draft_writer")
    call = of_type(read_events(events_file), "llm_call")[0]
    assert call["retries"] == 2 and call["agent"] == "draft_writer" and call["error"] is None


def test_auto_sinks(monkeypatch):
    monkeypatch.setattr(settings, "telemetry_sinks", "auto")
    monkeypatch.delenv("K_SERVICE", raising=False)
    assert telemetry.active_sinks() == {"log", "file"}
    monkeypatch.setenv("K_SERVICE", "email-generator-app")
    assert telemetry.active_sinks() == {"log"}, "no file sink on Cloud Run (in-memory disk)"


def test_json_formatter_adds_request_context():
    record = logging.LogRecord("telemetry", logging.INFO, __file__, 1, "hello", None, None)
    record.json_fields = {"event": "llm_call", "agent": "review"}
    record.request_id = "test-req-fmt1"
    line = JsonFormatter().format(record)
    payload = json.loads(line)
    assert payload["severity"] == "INFO" and payload["message"] == "hello"
    assert payload["request_id"] == "test-req-fmt1" and payload["event"] == "llm_call"
    assert "\n" not in line


def test_generate_endpoint_returns_request_id(events_file):
    import asyncio
    import httpx
    from src.api.main import app

    async def call():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            body = {"prompt": "Thank Sarah for the meeting", "use_stub": True, "save_to_history": False}
            return await client.post("/api/email/generate", json=body, headers={"X-Request-ID": "client-req-12345"})

    resp = asyncio.run(call())
    assert resp.status_code == 200
    assert resp.headers["x-request-id"] == "client-req-12345"
    assert resp.json()["metadata"]["request_id"] == "client-req-12345"
    s = of_type(read_events(events_file), "request_summary")[0]
    assert s["endpoint"] == "email.generate" and s["request_id"] == "client-req-12345"
