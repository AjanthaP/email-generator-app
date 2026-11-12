from types import SimpleNamespace

from src.agents.personalization import PersonalizationAgent


class FakePrompt:
    def __or__(self, _llm):
        return self


class FakeLLMWrapper:
    def invoke_chain(self, _chain, _params, **_kwargs):
        return SimpleNamespace(content=[
            {"type": "text", "text": "Dear Jane,"},
            {"type": "text", "text": "The updated draft."},
        ])


def test_personalize_extracts_text_from_content_blocks():
    agent = object.__new__(PersonalizationAgent)
    agent.get_profile = lambda _user_id: {
        "user_name": "Alex",
        "signature": "Best regards",
        "style_notes": "professional",
    }
    agent.prompt = FakePrompt()
    agent.llm = object()
    agent.llm_wrapper = FakeLLMWrapper()

    personalized = agent.personalize("Dear Jane,\nOriginal draft.", "test-user")

    assert personalized == "Dear Jane,\nThe updated draft."
