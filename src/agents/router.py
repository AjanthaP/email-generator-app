"""
Router Agent - Handles workflow routing and fallbacks.

This agent acts as a traffic controller in the workflow, deciding the next
steps, handling errors, managing retries, and providing fallback mechanisms
when primary processing fails.
"""

from typing import Dict, Literal, List
from langchain_google_genai import ChatGoogleGenerativeAI
import json
from src.utils.config import settings
from src.utils.prompts import ROUTER_AGENT_PROMPT


class RouterAgent:
    """
    Handles workflow routing and fallbacks.
    
    This agent:
    - Routes the workflow to next steps
    - Manages error handling and retries
    - Provides fallback drafts when LLMs fail
    - Controls conditional logic in the workflow
    
    The router is crucial for robustness, ensuring the system can gracefully
    handle failures and always provide a usable output.
    
    Example:
        >>> llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        >>> router = RouterAgent(llm)
        >>> next_step = router.route_next_step(state)
    """
    
    def __init__(self, llm: ChatGoogleGenerativeAI = None, max_retries: int = 3):
        """
        Initialize Router Agent.
        
        Args:
            llm: Optional ChatGoogleGenerativeAI instance (may not be needed)
            max_retries: Maximum number of retry attempts before fallback
        """
        self.llm = llm
        self.max_retries = max_retries
    
    def route_next_step(self, state: Dict) -> Literal["continue", "retry", "fallback"]:
        """
        Determine the next step in the workflow.
        
        Args:
            state: Current workflow state
            
        Returns:
            Literal: Next routing decision (continue, retry, or fallback)
        """
        # Check for errors
        if state.get("error"):
            retry_count = state.get("retry_count", 0)
            if retry_count < self.max_retries:
                return "retry"
            else:
                return "fallback"
        
        # Check if draft needs improvement
        if state.get("needs_improvement"):
            return "retry"
        
        # Check for issues from review agent
        metadata = state.get("metadata", {})
        if metadata.get("issues"):
            return "retry"
        
        return "continue"

    def _llm_decide(self, state: Dict) -> Dict:
        """Optional LLM-based decision pathway.

        Returns a dict with keys routing_decision and metadata.decision_reason if successful.
        Falls back to deterministic logic on error or invalid output.
        """
        if not settings.enable_llm_router or self.llm is None:
            return {"routing_decision": self.route_next_step(state), "metadata": {"llm_router_used": False}}

        retry_count = state.get("retry_count", 0)
        issues = (state.get("metadata", {}) or {}).get("issues", [])
        error = state.get("error")
        needs_improvement = state.get("needs_improvement")
        max_retries = self.max_retries

        summary = (
            f"error={error}; retry_count={retry_count}; max_retries={max_retries}; "
            f"needs_improvement={needs_improvement}; issues_count={len(issues)}; issues={issues[:5]}"
        )

        try:
            prompt = ROUTER_AGENT_PROMPT.format_messages(state_summary=summary)
            response = self.llm.invoke(prompt)
            raw = response.content.strip()
            # Attempt JSON parse; clean common formatting artifacts
            if raw.startswith("```"):
                raw = raw.strip("`")
                raw = raw.replace("json", "", 1).strip()
            data = json.loads(raw)
            decision = data.get("decision")
            reason = data.get("reason", "")
            if decision not in {"continue", "retry", "fallback"}:
                raise ValueError("Invalid decision from LLM")
            return {
                "routing_decision": decision,
                "metadata": {
                    "llm_router_used": True,
                    "decision_reason": reason,
                },
            }
        except Exception as e:
            # Fallback to deterministic logic
            deterministic = self.route_next_step(state)
            return {
                "routing_decision": deterministic,
                "metadata": {
                    "llm_router_used": False,
                    "llm_router_error": str(e)[:200],
                },
            }
    
    def create_fallback_draft(self, state: Dict) -> str:
        """
        Create fallback draft when LLM processing fails.
        
        This ensures the system always returns something usable, even if
        all agents fail. The fallback uses direct template substitution
        with no LLM calls.
        
        Args:
            state: Current workflow state with parsed_data
            
        Returns:
            str: Basic but valid email draft
        """
        parsed = state.get("parsed_data", {})
        recipient = parsed.get("recipient_name", "there")
        purpose = parsed.get("email_purpose", "reach out")
        key_points = parsed.get("key_points", [])
        
        fallback = f"""Dear {recipient},

I hope this email finds you well.

I wanted to {purpose}.

"""
        
        if key_points:
            for point in key_points:
                fallback += f"• {point}\n"
            fallback += "\n"
        
        fallback += """I look forward to hearing from you.

Best regards"""
        
        return fallback
    
    def validate_state(self, state: Dict) -> tuple[bool, List[str]]:
        """
        Validate workflow state for completeness.
        
        Args:
            state: Current workflow state
            
        Returns:
            Tuple of (is_valid, list_of_missing_fields)
        """
        required_fields = ["user_input", "parsed_data", "intent", "draft"]
        missing = [f for f in required_fields if f not in state or state[f] is None]
        
        return len(missing) == 0, missing
    
    def __call__(self, state: Dict) -> Dict:
        """
        LangGraph node function - handles routing logic.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dict: Updated state with routing decision and possible fallback
        """
        # Validate state first
        is_valid, missing = self.validate_state(state)
        
        if not is_valid:
            print(f"Warning: Missing fields in state: {missing}")
        
        # Decide next step (LLM or deterministic)
        decision_payload = self._llm_decide(state)
        next_step = decision_payload.get("routing_decision")
        
        # If fallback is needed, create fallback draft
        if next_step == "fallback":
            return {
                "final_draft": self.create_fallback_draft(state),
                "metadata": {
                    "fallback_used": True,
                    "reason": state.get("error", "Max retries exceeded"),
                    "approved": False,
                    "issues": ["Fallback draft used due to processing errors"]
                },
                "routing_decision": "fallback"
            }
        
        return decision_payload
