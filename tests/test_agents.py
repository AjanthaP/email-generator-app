"""Pytest-based structural tests replaced by lightweight integration tests.

This file now provides a minimal smoke test to ensure critical agents
instantiate and basic methods execute without raising.
"""
from src.utils.config import settings
from src.agents.input_parser import InputParserAgent
from src.agents.intent_detector import IntentDetectorAgent
from src.agents.draft_writer import DraftWriterAgent


class DummyLLM:
    model = "stub"

def _llm():
    import os; os.environ["DONOTUSEGEMINI"] = "1"; return DummyLLM()


def test_parse_and_detect():
    llm = _llm()
    parser = InputParserAgent(llm)
    detector = IntentDetectorAgent(llm)
    parsed = parser.parse("Write an email to John about meeting tomorrow")  # falls back to stub parse
    assert parsed.recipient_name
    intent = detector.detect({"email_purpose": parsed.email_purpose, "key_points": [], "context": ""})
    assert intent in {"follow_up", "outreach", "update", "apology", "request", "meeting_request"}


def test_draft_writer_basic():
    llm = _llm()
    writer = DraftWriterAgent(llm)
    parsed_data = {
        "recipient_name": "Jane Doe",
        "email_purpose": "introduce AI consulting services",
        "key_points": ["expertise in ML", "free consultation"],
        "context": "cold outreach",
    }
    draft = writer.write("outreach", parsed_data, "formal")  # uses fallback draft generation
    assert "Jane" in draft or "Doe" in draft or "Dear" in draft
    assert len(draft.split()) > 20


if __name__ == "__main__":
    test_parse_and_detect(); test_draft_writer_basic(); print("✅ Minimal agent tests passed")
