from typing import TypedDict, Any, Dict, Callable, Optional
import os
import sys

from langchain_google_genai import ChatGoogleGenerativeAI

from src.utils.config import settings
from src.agents.input_parser import InputParserAgent
from src.agents.intent_detector import IntentDetectorAgent
from src.agents.draft_writer import DraftWriterAgent
from src.agents.tone_stylist import ToneStylistAgent
from src.agents.personalization import PersonalizationAgent
from src.agents.review_agent import ReviewAgent
from src.agents.refinement import RefinementAgent
from src.agents.router import RouterAgent
from src.utils.llm_wrapper import make_wrapper, LLMWrapper
from src.utils.observability import activate_langsmith


class EmailState(TypedDict, total=False):
    """TypedDict representing the workflow state for an email generation."""
    user_input: str
    user_id: str
    parsed_data: Dict[str, Any]
    recipient: str
    intent: str
    draft: str
    tone: str
    personalized_draft: str
    review_notes: Dict[str, Any]
    next_step: str


def _init_llm() -> ChatGoogleGenerativeAI:
    """Initialize the LLM using settings from config.
    
    NOTE: This should only be called when we're actually going to use the LLM,
    as instantiation may trigger validation calls to the Gemini API.
    """
    # Activate tracing once if configured
    activate_langsmith()
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=settings.temperature,
        max_output_tokens=settings.max_tokens,
    )


def create_agents(llm: ChatGoogleGenerativeAI) -> Dict[str, Callable[[Dict], Dict]]:
    """Create and return instantiated agent callables keyed by name."""
    wrapper: LLMWrapper = make_wrapper(llm)

    input_parser = InputParserAgent(llm, llm_wrapper=wrapper)
    intent_detector = IntentDetectorAgent(llm, llm_wrapper=wrapper)
    draft_writer = DraftWriterAgent(llm, llm_wrapper=wrapper)
    tone_stylist = ToneStylistAgent(llm, llm_wrapper=wrapper)
    personalization = PersonalizationAgent(llm, llm_wrapper=wrapper)
    review = ReviewAgent(llm, llm_wrapper=wrapper)
    refinement = RefinementAgent(llm, llm_wrapper=wrapper)
    router = RouterAgent(llm)

    return {
        "input_parser": input_parser,
        "intent_detector": intent_detector,
        "draft_writer": draft_writer,
        "tone_stylist": tone_stylist,
        "personalization": personalization,
        "review": review,
        "refinement": refinement,
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
        "refinement",
        "router",
    ]


def _detect_no_gemini_flag() -> bool:
    """Detect whether the environment or command-line requests a non-Gemini run.

    Checks (in order):
    - Environment variable `DONOTUSEGEMINI` or `NO_GEMINI` set to a truthy value
    - Command-line flag `-donotusegemini` present in sys.argv
    """
    env_val = os.environ.get("DONOTUSEGEMINI") or os.environ.get("NO_GEMINI")
    if env_val and env_val.lower() in ("1", "true", "yes", "y"):
        return True

    # Check command-line args
    if any(arg.lower() == "-donotusegemini" for arg in sys.argv[1:]):
        return True

    return False


def _generate_stub_state(user_input: str, tone: str = "formal") -> EmailState:
    """Create a lightweight stubbed state (no LLM calls) for local testing.

    This function produces reasonable defaults for parsed_data, intent, and a basic draft.
    It's intentionally simplistic and intended only for local UI/testing when Gemini is unavailable.
    """
    # Try to extract recipient from a prefixed line
    recipient = "Recipient"
    recipient_email = ""
    lines = [ln.strip() for ln in user_input.splitlines() if ln.strip()]
    for ln in lines[:3]:
        if ln.lower().startswith("recipient email:"):
            recipient_email = ln.split(":", 1)[1].strip()
        if ln.lower().startswith("recipient:"):
            recipient = ln.split(":", 1)[1].strip()

    # Simple intent heuristics
    text = user_input.lower()
    if "follow" in text or "follow-up" in text:
        intent = "follow_up"
    elif "thank" in text:
        intent = "thank_you"
    elif "meeting" in text or "schedule" in text:
        intent = "meeting_request"
    elif "apolog" in text:
        intent = "apology"
    elif "update" in text or "status" in text:
        intent = "status_update"
    else:
        intent = "outreach"

    # Key points: take first 2 short lines or first sentence fragments
    key_points = []
    for ln in lines:
        if len(key_points) >= 4:
            break
        if len(ln) > 20:
            key_points.append(ln if len(ln) < 120 else ln[:120])

    if not key_points:
        # fallback: split by sentences
        key_points = [s.strip() for s in user_input.replace("\n", " ").split(".") if s.strip()][:3]

    purpose = key_points[0] if key_points else text[:120]

    draft_lines = [f"Dear {recipient},\n\n"]
    draft_lines.append(f"{purpose}.\n\n")
    if key_points:
        for p in key_points:
            draft_lines.append(f"• {p}\n")
        draft_lines.append("\n")

    draft_lines.append("I look forward to hearing from you.\n\nBest regards")

    draft = "".join(draft_lines)

    state: EmailState = {
        "user_input": user_input,
        "parsed_data": {
            "recipient_name": recipient,
            "recipient_email": recipient_email,
            "email_purpose": purpose,
            "key_points": key_points,
            "tone_preference": tone,
            "constraints": {},
            "context": "stubbed"
        },
        "recipient": recipient,
        "intent": intent,
        "draft": draft,
        "tone": tone,
        "personalized_draft": draft,
        "final_draft": draft,
    }

    # Metadata to indicate this is a local stubbed response
    state["metadata"] = {"source": "stub", "model": None}

    return state


def execute_workflow(user_input: str, llm: Optional[ChatGoogleGenerativeAI] = None, use_stub: Optional[bool] = None, user_id: str = "default", developer_mode: bool = False) -> EmailState:
    """Execute the email workflow sequentially and return the final state.

    If `use_stub` is True, the function will generate a stubbed state without calling the LLMs.
    If `use_stub` is None, it will auto-detect via environment variables or command-line flag.
    
    Args:
        user_input: The user's email request
        llm: Optional LLM instance to use
        use_stub: Whether to use stub mode (no LLM calls)
        user_id: User ID for profile personalization (default: "default")
    """
    if use_stub is None:
        use_stub = _detect_no_gemini_flag()

    if use_stub:
        # Return a stubbed state for local testing without hitting Gemini
        # IMPORTANT: Return early BEFORE creating any LLM instance
        return _generate_stub_state(user_input)

    # Only create LLM if we're NOT using stub mode
    if llm is None:
        llm = _init_llm()

    agents = create_agents(llm)
    order = default_graph_order()

    # Initialize state with user_id
    state: EmailState = {"user_input": user_input, "tone": "formal", "user_id": user_id}
    
    # Debug log
    print(f"[Workflow] Executing with user_id: {user_id}")

    # Attach metadata indicating we're attempting to use the LLM by default.
    # If a quota fallback happens later, this will be updated to indicate stub.
    state["metadata"] = {"source": "llm", "model": settings.gemini_model}

    def _is_quota_error(exc: Exception) -> bool:
        """Heuristic to detect Gemini quota / 429 ResourceExhausted errors.

        We keep this lightweight: look for common substrings. If detected,
        we'll fall back to the local stubbed generator to avoid a broken state.
        """
        msg = str(exc).lower()
        if not msg:
            return False
        keywords = ["quota", "429", "resourceexhausted", "you exceeded", "generate_content_free_tier"]
        return any(k in msg for k in keywords)

    # Run agents in order, merging returned updates into state
    # Developer trace collection
    developer_trace: list[dict[str, Any]] = []

    for node_name in order:
        agent = agents.get(node_name)
        if agent is None:
            continue

        try:
            updates = agent(state) or {}
            # Merge updates into state
            for k, v in updates.items():
                state[k] = v  # type: ignore[index]

            if developer_mode:
                # Capture a snapshot after this agent runs
                snapshot_keys = [
                    "parsed_data", "intent", "draft", "tone", "personalized_draft",
                    "final_draft", "metadata"
                ]
                snapshot = {k: state.get(k) for k in snapshot_keys if k in state}
                developer_trace.append({
                    "agent": node_name,
                    "snapshot": snapshot
                })
        except Exception as e:
            # If it's a Gemini quota/429 error, switch to the stubbed generator
            # immediately and return a usable state rather than continuing with
            # missing/partial fields.
            state.setdefault("review_notes", {})
            state["review_notes"][node_name] = {"error": str(e)}

            if _is_quota_error(e):
                state["review_notes"]["gemini_quota_fallback"] = {
                    "message": "Detected Gemini quota / 429 error and falling back to local stubbed generator.",
                    "original_error": str(e),
                }
                # Return a stubbed state which provides parsed_data, intent and a basic draft
                stub_state = _generate_stub_state(user_input, tone=state.get("tone", "formal"))
                # Attach the review notes to stub_state so callers know why fallback occurred
                stub_state.setdefault("review_notes", {})
                stub_state["review_notes"].update(state.get("review_notes", {}))
                # Update metadata to indicate source is now stub but record the attempted model
                stub_state.setdefault("metadata", {})
                stub_state["metadata"].update({"source": "stub", "fallback_from_model": settings.gemini_model})
                if developer_mode:
                    stub_state["developer_trace"] = developer_trace
                return stub_state

            # Non-quota error: capture and continue to next agent (best-effort)
            # This keeps the workflow robust when a single agent fails.

    if developer_mode:
        state["developer_trace"] = developer_trace
    return state


__all__ = ["EmailState", "execute_workflow", "create_agents", "default_graph_order"]


def generate_email(user_input: str, tone: str = "formal", use_stub: Optional[bool] = None, user_id: str = "default", developer_mode: bool = False) -> Dict[str, Any]:
    """Convenience wrapper matching the v2 guide's example signature.

    This wraps `execute_workflow` and returns a simplified dict containing
    the final draft plus any metadata. Falls back through the same stub path
    when `use_stub` is True or quota errors are detected.

    Args:
        user_input: Raw user prompt / description.
        tone: Desired tone (formal, casual, assertive, empathetic, etc.).
        use_stub: Force stub mode (no external LLM calls). If None, autodetect.
        user_id: User ID for profile personalization (default: "default")

    Returns:
        Dict with keys:
            - final_draft: str (best available draft)
            - metadata: dict (source/model/fallback info)
            - review_notes: optional dict of agent-level errors/fallback reasons
    """
    state = execute_workflow(user_input, use_stub=use_stub, user_id=user_id, developer_mode=developer_mode)
    # Choose best available draft key
    final = state.get("final_draft") or state.get("personalized_draft") or state.get("styled_draft") or state.get("draft") or ""
    result = {
        "final_draft": final,
        "metadata": state.get("metadata", {}),
        "review_notes": state.get("review_notes", {}),
    }
    if developer_mode:
        result["developer_trace"] = state.get("developer_trace", [])
    return result

__all__.append("generate_email")
