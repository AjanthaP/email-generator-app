import pytest
from src.workflow.langgraph_flow import execute_workflow

class FakeQuotaError(Exception):
    pass


def test_quota_error_triggers_stub(monkeypatch):
    # Ensure stub flag not set so workflow attempts normal path before fallback
    import os
    os.environ.pop("DONOTUSEGEMINI", None)
    # Monkeypatch one agent to raise a quota-like error on call
    from src.agents.input_parser import InputParserAgent

    original_call = InputParserAgent.__call__

    def quota_fail(self, state):
        raise FakeQuotaError("429 ResourceExhausted: You exceeded your current quota")

    monkeypatch.setattr(InputParserAgent, "__call__", quota_fail)

    state = execute_workflow("Write a follow up email to thank Sarah for the meeting", use_stub=False)

    assert state.get("metadata", {}).get("source") == "stub", "Should fall back to stub source"
    assert "gemini_quota_fallback" in state.get("review_notes", {}), "Review notes should record fallback reason"
    assert state.get("final_draft"), "Stub state should include a final draft"

    # Restore original for cleanliness
    monkeypatch.setattr(InputParserAgent, "__call__", original_call)
