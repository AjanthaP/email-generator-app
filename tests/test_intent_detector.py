from src.agents.intent_detector import EmailIntent, IntentDetectorAgent
from src.agents.draft_writer import DraftWriterAgent
from types import SimpleNamespace


class FakePrompt:
    def __or__(self, _llm):
        return self


class FakeLLM:
    def invoke(self, _prompt):
        return None


class FakeLLMWrapper:
    def invoke_chain(self, _chain, _params):
        return SimpleNamespace(content="unsupported_category")


def test_sick_leave_request_is_not_classified_as_outreach():
    detector = object.__new__(IntentDetectorAgent)
    result = detector({
        "parsed_data": {"email_purpose": "An opportunity to discuss strategic growth"},
        "user_input": "request for a sick leave due to cold",
    })

    assert result["intent"] == EmailIntent.LEAVE_REQUEST.value


def test_leave_request_fallback_draft_uses_requested_intent():
    writer = object.__new__(DraftWriterAgent)
    draft = writer._fallback_draft(
        {
            "recipient_name": "Manager",
            "original_request": "request for a sick leave due to cold",
        },
        EmailIntent.LEAVE_REQUEST.value,
    )

    assert "request sick leave due to a cold" in draft.lower()
    assert "strategic growth" not in draft.lower()


def test_leave_request_uses_dedicated_prompt():
    writer = DraftWriterAgent(llm=object(), llm_wrapper=object())

    assert "leave_request" in writer.intent_templates
    assert "{original_request}" in writer.intent_templates["leave_request"]


def test_unrecognized_intent_uses_generic_category():
    detector = object.__new__(IntentDetectorAgent)
    detector.llm = FakeLLM()
    detector.llm_wrapper = FakeLLMWrapper()
    detector.prompt = FakePrompt()
    detector.intents = [intent.value for intent in EmailIntent]

    assert detector.detect({"email_purpose": "Write a note about a new topic"}) == "generic"


def test_generic_intent_uses_original_request_without_outreach_template():
    writer = object.__new__(DraftWriterAgent)
    request = "Please email my landlord about fixing the kitchen sink."
    draft = writer._fallback_draft(
        {"recipient_name": "Landlord", "original_request": request},
        "generic",
    )

    assert request in draft
    assert "value proposition" not in draft.lower()
