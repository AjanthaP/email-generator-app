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
            # Return original draft if refinement fails
            return draft
    
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
