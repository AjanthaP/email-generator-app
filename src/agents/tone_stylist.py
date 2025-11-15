"""
Tone Stylist Agent - Adjusts email tone while preserving content.

This agent takes a generated email draft and transforms it to match the
desired tone (formal, casual, assertive, empathetic). It maintains the
core message while changing vocabulary, structure, and style.
"""

from typing import Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from src.utils.prompts import TONE_STYLIST_PROMPT
from src.utils.llm_wrapper import LLMWrapper, make_wrapper


class ToneStylistAgent:
    """
    Adjusts email tone while preserving the core message.
    
    This agent is responsible for tone transformation. It takes a generic
    draft and rewrites it to match specific tone preferences. Tone adjustment
    includes changes to:
    - Vocabulary and word choice
    - Sentence structure
    - Greeting and closing formality
    - Emotional tone and emphasis
    - Professional level
    
    Supported tones:
    - formal: Professional, structured, no contractions
    - casual: Friendly, conversational, relaxed
    - assertive: Direct, confident, action-oriented
    - empathetic: Understanding, supportive, warm
    
    Example:
        >>> llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        >>> stylist = ToneStylistAgent(llm)
        >>> styled = stylist.adjust_tone(draft, "casual")
    """
    
    # Tone configuration guidelines
    TONE_GUIDELINES = {
        "formal": {
            "characteristics": "Professional, structured, no contractions, proper titles",
            "vocabulary": "sophisticated, traditional business language",
            "structure": "well-organized with clear paragraphs",
            "greeting": "Dear [Name] / Dear Sir/Madam",
            "closing": "Sincerely / Best regards / Respectfully"
        },
        "casual": {
            "characteristics": "Friendly, conversational, use contractions",
            "vocabulary": "simple, everyday language",
            "structure": "natural flow, shorter paragraphs",
            "greeting": "Hi [Name] / Hey [Name]",
            "closing": "Thanks / Cheers / Best"
        },
        "assertive": {
            "characteristics": "Direct, confident, action-oriented, clear",
            "vocabulary": "strong action verbs, decisive language",
            "structure": "bullet points, clear CTAs",
            "greeting": "Hello [Name]",
            "closing": "Looking forward to your response / Let's move forward"
        },
        "empathetic": {
            "characteristics": "Understanding, supportive, compassionate",
            "vocabulary": "warm, acknowledging feelings",
            "structure": "gentle flow, validating statements",
            "greeting": "Dear [Name]",
            "closing": "With understanding / Warm regards"
        }
    }
    
    def __init__(self, llm: ChatGoogleGenerativeAI, llm_wrapper: Optional[LLMWrapper] = None):
        """
        Initialize Tone Stylist Agent.
        
        Args:
            llm: ChatGoogleGenerativeAI instance for processing
        """
        self.llm = llm
        self.llm_wrapper = llm_wrapper or make_wrapper(llm)
        # Use shared tone stylist prompt
        self.prompt = TONE_STYLIST_PROMPT
    
    def adjust_tone(self, draft: str, tone: str) -> str:
        """
        Adjust email tone.
        
        Args:
            draft: Original email draft
            tone: Target tone (formal, casual, assertive, empathetic)
            
        Returns:
            str: Email draft with adjusted tone
        """
        try:
            # Get tone-specific guidelines
            guidelines = self.TONE_GUIDELINES.get(tone, self.TONE_GUIDELINES["formal"])
            
            chain = self.prompt | self.llm
            # Determine effective target length (fallback 170), floor to 25 if <10
            target = getattr(self, "_workflow_length", None)
            if target is None:
                target = 170
            elif isinstance(target, int) and target < 10:
                target = 25

            response = self.llm_wrapper.invoke_chain(chain, {
                "draft": draft,
                "tone": tone,
                "target_length": target,
                **guidelines
            })
            
            return response.content.strip()
            
        except Exception as e:
            print(f"Error adjusting tone: {e}")
            # Return original draft if tone adjustment fails
            return draft
    
    def __call__(self, state: Dict) -> Dict:
        """
        LangGraph node function - processes state and returns updates.
        
        Args:
            state: Current workflow state with draft and tone
            
        Returns:
            Dict: Updated state with tone-adjusted draft
        """
        # Surface workflow length to adjust_tone
        self._workflow_length = state.get("length_preference")  # type: ignore[attr-defined]
        styled_draft = self.adjust_tone(
            state["draft"],
            state.get("tone", "formal")
        )
        return {"styled_draft": styled_draft}
