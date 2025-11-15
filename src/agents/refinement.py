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
        """
        Refine email draft by fixing specific issues.
        
        This method applies the refinement process to:
        1. Remove duplicate signatures
        2. Fix grammar and spelling errors
        3. Eliminate repetitive sentences
        
        Args:
            draft: Email draft to refine
            
        Returns:
            str: Refined email draft
        """
        from src.utils.config import settings
        # Stub/local mode: perform lightweight deterministic cleanup without LLM
        if getattr(settings, "donotusegemini", False) or not hasattr(self.llm, "invoke"):
            return self._local_cleanup(draft)
        try:
            # Create chain with refinement prompt
            chain = REFINEMENT_AGENT_PROMPT | self.llm

            # Invoke with wrapper
            response = self.llm_wrapper.invoke_chain(chain, {
                "draft": draft
            })

            # Extract refined content
            refined_draft = response.content.strip()

            # If refinement returns empty or suspiciously short (less than 30% of original), return original
            # This prevents over-aggressive condensation
            if not refined_draft or len(refined_draft) < len(draft) * 0.3:
                print("Warning: Refinement produced suspiciously short output, returning original")
                return draft

            return refined_draft

        except Exception as e:
            print(f"Error refining draft: {e}")
            # Return local cleanup version if refinement fails
            return self._local_cleanup(draft)

    def _local_cleanup(self, draft: str) -> str:
        """Non-LLM cleanup used in stub mode.

        Implements:
        - Duplicate signature removal (e.g., repeated 'Best regards,' blocks)
        - Collapsing repeated consecutive sentences
        """
        lines = draft.splitlines()
        cleaned: list[str] = []
        signature_seen = False
        prev_norm = ""
        skip_next_name = False
        for i, line in enumerate(lines):
            norm = line.strip().lower()
            # Skip orphaned name line after a skipped duplicate signature
            if skip_next_name:
                if norm and "," not in norm and not norm.startswith("dear"):
                    skip_next_name = False
                    continue
                skip_next_name = False
            if norm.startswith("best regards") or norm.startswith("kind regards"):
                if signature_seen:
                    # Skip duplicate signature block entirely
                    # Also signal to skip following name line if present
                    skip_next_name = True
                    continue
                signature_seen = True
                cleaned.append(line)
                # Include at most one name line directly after signature
                if i + 1 < len(lines):
                    name_line = lines[i+1].strip()
                    if name_line and not name_line.lower().startswith("dear") and "," not in name_line.lower():
                        cleaned.append(name_line)
                continue
            # Skip standalone duplicate name lines following an already captured signature
            if signature_seen and prev_norm.startswith("best regards") and norm and "," not in norm and not norm.startswith("dear"):
                # first name already added, skip duplicates
                if norm in {l.strip().lower() for l in cleaned[-2:]}:
                    continue
            # Skip immediate exact duplicate lines
            if norm and norm == prev_norm:
                continue
            cleaned.append(line)
            prev_norm = norm
        import re
        result = "\n".join(cleaned)
        # Collapse duplicate name lines after signature
        result = re.sub(r'(Best regards,\n)([A-Za-z .]+)(?:\n\2)+', r'\1\2', result, flags=re.IGNORECASE)
        return result
    
    def __call__(self, state: Dict) -> Dict:
        """
        LangGraph node function - processes state and returns updates.
        
        Args:
            state: Current workflow state with final_draft
            
        Returns:
            Dict: Updated state with refined final_draft
        """
        # Get the draft to refine (from final_draft after review/personalization)
        draft_to_refine = state.get("final_draft", "")
        
        if not draft_to_refine:
            print("Warning: No final_draft found in state for refinement")
            return {"final_draft": state.get("draft", "")}
        
        # Apply refinement
        refined_draft = self.refine(draft_to_refine)
        
        return {
            "final_draft": refined_draft,
            "metadata": {
                "refined": True
            }
        }
