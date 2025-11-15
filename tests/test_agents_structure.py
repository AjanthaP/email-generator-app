"""Structural validation for agents (simplified)."""
from src.utils.config import settings  # settings still needed for model name if referenced
from src.agents.input_parser import InputParserAgent
from src.agents.intent_detector import IntentDetectorAgent, EmailIntent
from src.agents.draft_writer import DraftWriterAgent
from src.agents.tone_stylist import ToneStylistAgent
from src.agents.personalization import PersonalizationAgent
from src.agents.review_agent import ReviewAgent
from src.agents.router import RouterAgent


class DummyLLM:
    model = "stub"

def _llm():
    # Force stub mode
    import os; os.environ["DONOTUSEGEMINI"] = "1"
    return DummyLLM()


def test_agent_instantiation():
    llm = _llm()
    InputParserAgent(llm)
    IntentDetectorAgent(llm)
    DraftWriterAgent(llm)
    ToneStylistAgent(llm)
    PersonalizationAgent(llm)
    ReviewAgent(llm)
    RouterAgent(llm)


def test_intent_enum_nonempty():
    assert len([i.value for i in EmailIntent]) > 0

if __name__ == "__main__":
    test_agent_instantiation(); test_intent_enum_nonempty(); print("✅ Agent structure tests passed")
