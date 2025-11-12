import pytest
from src.agents.input_parser import InputParserAgent
from src.agents.intent_detector import IntentDetectorAgent
from src.agents.draft_writer import DraftWriterAgent
from langchain_google_genai import ChatGoogleGenerativeAI
from src.utils.llm_wrapper import make_wrapper
from src.utils.config import settings


@pytest.fixture
def llm():
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key
    )


@pytest.fixture
def wrapper(llm):
    return make_wrapper(llm, max_retries=1, initial_backoff=0.1)


class TestInputParser:
    def test_parse_basic_input(self, llm):
        agent = InputParserAgent(llm)
        result = agent.parse("Write an email to John about meeting tomorrow")

        assert result.recipient_name
        assert "meeting" in result.email_purpose.lower()

    def test_parse_with_tone(self, llm):
        agent = InputParserAgent(llm)
        result = agent.parse("Write a casual email to Sarah about the project")

        assert result.tone_preference in ["casual", "formal", "assertive", "empathetic"]


class TestIntentDetector:
    def test_detect_outreach_intent(self, llm):
        agent = IntentDetectorAgent(llm)
        parsed_data = {
            "email_purpose": "introduce our services to potential client",
            "key_points": ["AI consulting", "free consultation"],
            "context": "cold outreach"
        }

        intent = agent.detect(parsed_data)
        assert intent == "outreach"

    def test_detect_followup_intent(self, llm):
        agent = IntentDetectorAgent(llm)
        parsed_data = {
            "email_purpose": "follow up on last week's meeting",
            "key_points": ["thank you", "next steps"],
            "context": "post-meeting"
        }

        intent = agent.detect(parsed_data)
        assert intent == "follow_up"


class TestDraftWriter:
    def test_write_outreach_draft(self, llm):
        agent = DraftWriterAgent(llm)
        parsed_data = {
            "recipient_name": "Jane Doe",
            "email_purpose": "introduce AI consulting services",
            "key_points": ["expertise in ML", "free consultation"]
        }

        draft = agent.write("outreach", parsed_data, "formal")

        assert any(name in draft for name in ["Jane", "Doe"]) or "Dear" in draft
        assert len(draft.split()) > 50
        assert any(draft.strip().endswith(x) for x in ("regards", "Regards", "sincerely", "Sincerely", "Best regards"))
