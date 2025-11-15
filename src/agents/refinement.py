"""
Refinement Agent - Final polish for email drafts.

This agent performs final refinement on generated emails, specifically:
1. Removing duplicate signatures
2. Fixing grammar and spelling errors
3. Eliminating repetitive sentences

This is the last step in the email generation pipeline, ensuring
the final output is polished and professional.
"""

from typing import Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from src.utils.prompts import REFINEMENT_AGENT_PROMPT
from src.utils.llm_wrapper import LLMWrapper, make_wrapper


class RefinementAgent:
    """
    Performs final refinement on email drafts.
    
    This agent acts as the final quality control step, specifically targeting:
    - Duplicate signatures (common when personalization adds signature to already-signed draft)
    - Grammar and spelling errors
    - Repetitive sentences or redundant content
    
    The agent is non-destructive - it preserves tone, intent, and key content
    while only fixing the specific issues it's designed to address.
    
    Example:
        >>> llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        >>> refiner = RefinementAgent(llm)
        >>> refined = refiner.refine(draft)
        >>> print(refined)
    """
    
    def __init__(self, llm: ChatGoogleGenerativeAI, llm_wrapper: Optional[LLMWrapper] = None):
        """
        Initialize Refinement Agent.
        
        Args:
            llm: ChatGoogleGenerativeAI instance for processing
            llm_wrapper: Optional LLM wrapper for consistent invocation
        """
        self.llm = llm
        self.llm_wrapper = llm_wrapper or make_wrapper(llm)
    
    def refine(self, draft: str) -> str:
        """Refine email draft strictly via prompt-guided LLM.

        All duplicate removal, greeting/sig normalization, grammar fixes, and
        repetition pruning are delegated to the refinement prompt. This agent
        intentionally avoids hardcoded text mutation logic to keep behavior
        model-driven and adaptable.

        Fallback: If the LLM is unavailable or errors, the original draft is
        returned unchanged to avoid accidental destructive edits.
        """
        from src.utils.config import settings
        # If in stub mode or no invoke capability, return original unchanged
        if getattr(settings, "donotusegemini", False) or not hasattr(self.llm, "invoke"):
            return draft
        try:
            chain = REFINEMENT_AGENT_PROMPT | self.llm
            response = self.llm_wrapper.invoke_chain(chain, {"draft": draft})
            refined = response.content.strip()
            # Guard against pathological over-trimming
            if not refined or len(refined) < len(draft) * 0.3:
                print("[RefinementAgent] Guard triggered: overly short refinement; using original")
                return draft
            return refined
        except Exception as e:
            print(f"[RefinementAgent] LLM error during refinement: {e}. Returning original draft.")
            return draft

    # Legacy local cleanup removed per user request; prompt-only refinement now.
    
    def __call__(self, state: Dict) -> Dict:
        """
        LangGraph node function - processes state and returns updates.
        
        Args:
            state: Current workflow state with final_draft
            
        Returns:
            Dict: Updated state with refined final_draft
        """
        # Get the draft to refine - try multiple sources in priority order
        draft_to_refine = (
            state.get("final_draft") or 
            state.get("personalized_draft") or 
            state.get("styled_draft") or 
            state.get("draft", "")
        )
        
        if not draft_to_refine:
            print("[RefinementAgent] Warning: No draft found in state for refinement")
            return {}
        
        print(f"[RefinementAgent] Refining draft (length: {len(draft_to_refine)} chars)")
        
        # Apply refinement
        refined_draft = self.refine(draft_to_refine)
        
        print(f"[RefinementAgent] Refinement complete (length: {len(refined_draft)} chars)")
        
        # Merge metadata instead of replacing
        current_metadata = state.get("metadata", {})
        if not isinstance(current_metadata, dict):
            current_metadata = {}
        
        return {
            "final_draft": refined_draft,
            "metadata": {
                **current_metadata,
                "refined": True
            }
        }
