from typing import TypedDict, Any, Dict, Callable
from langchain_google_genai import ChatGoogleGenerativeAI

from src.utils.config import settings
from src.agents.input_parser import InputParserAgent
from src.agents.intent_detector import IntentDetectorAgent
from src.agents.draft_writer import DraftWriterAgent
from src.agents.tone_stylist import ToneStylistAgent
from src.agents.personalization import PersonalizationAgent
from src.agents.review_agent import ReviewAgent
from src.agents.router import RouterAgent


class EmailState(TypedDict, total=False):
    """TypedDict representing the workflow state for an email generation."""
    user_input: str
    parsed_data: Dict[str, Any]
    recipient: str
    intent: str
    draft: str
    tone: str
    personalized_draft: str
    review_notes: Dict[str, Any]
    next_step: str


def _init_llm() -> ChatGoogleGenerativeAI:
    """Initialize the LLM using settings from config."""
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=settings.temperature,
        max_output_tokens=settings.max_tokens,
    )


def create_agents(llm: ChatGoogleGenerativeAI) -> Dict[str, Callable[[Dict], Dict]]:
    """Create and return instantiated agent callables keyed by name."""
    input_parser = InputParserAgent(llm)
    intent_detector = IntentDetectorAgent(llm)
    draft_writer = DraftWriterAgent(llm)
    tone_stylist = ToneStylistAgent(llm)
    personalization = PersonalizationAgent(llm)
    review = ReviewAgent(llm)
    router = RouterAgent(llm)

    return {
        "input_parser": input_parser,
        "intent_detector": intent_detector,
        "draft_writer": draft_writer,
        "tone_stylist": tone_stylist,
        "personalization": personalization,
        "review": review,
        "router": router,
    }


def default_graph_order() -> list[str]:
    """Return a default ordered list of agent node names for the workflow."""
    return [
        "input_parser",
        "intent_detector",
        "draft_writer",
        "tone_stylist",
        "personalization",
        "review",
        "router",
    ]


def execute_workflow(user_input: str, llm: ChatGoogleGenerativeAI | None = None) -> EmailState:
    """Execute the email workflow sequentially and return the final state.

    This is a simple LangGraph-like runner that calls each agent node in order.
    Agents receive the current state dict and should return a dict of updates
    which will be merged into the state.
    """
    if llm is None:
        llm = _init_llm()

    agents = create_agents(llm)
    order = default_graph_order()

    # Initialize state
    state: EmailState = {"user_input": user_input, "tone": "formal"}

    # Run agents in order, merging returned updates into state
    for node_name in order:
        agent = agents.get(node_name)
        if agent is None:
            continue

        try:
            updates = agent(state) or {}
            # Merge updates into state
            for k, v in updates.items():
                state[k] = v  # type: ignore[index]
        except Exception as e:
            # On error, capture review_notes and continue
            state.setdefault("review_notes", {})
            state["review_notes"][node_name] = {"error": str(e)}

    return state


__all__ = ["EmailState", "execute_workflow", "create_agents", "default_graph_order"]
