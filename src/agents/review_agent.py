"""
Review Agent - Validates and improves email drafts.

This agent performs quality assurance on the generated emails, checking for
grammar, clarity, tone alignment, and completeness. It can suggest improvements
or return the draft as-is if it meets quality standards.
"""

from typing import Dict, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import re
from src.utils.llm_wrapper import LLMWrapper, make_wrapper


class ReviewAgent:
    """
    Validates and improves email drafts.
    
    This agent acts as a quality control checkpoint. It:
    - Checks for grammatical errors
    - Validates tone alignment
    - Ensures all key points are included
    - Verifies clarity and structure
    - Suggests improvements when needed
    
    The agent uses both LLM-based review and heuristic validation to
    ensure high-quality email output.
    
    Example:
        >>> llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        >>> reviewer = ReviewAgent(llm)
        >>> result = reviewer.review(draft, "formal", "outreach")
        >>> print(result["final_draft"])
    """
    
    def __init__(self, llm: ChatGoogleGenerativeAI, llm_wrapper: Optional[LLMWrapper] = None):
        """
        Initialize Review Agent.
        
        Args:
            llm: ChatGoogleGenerativeAI instance for processing
        """
        self.llm = llm
        self.llm_wrapper = llm_wrapper or make_wrapper(llm)
        self.review_prompt = ChatPromptTemplate.from_template("""
        You are an expert email reviewer and editor. Analyze this email draft and improve it if needed.
        
        Email Draft:
        {draft}
        
        Expected Tone: {tone}
        Expected Intent: {intent}
        
        Review Criteria:
        1. Tone Alignment: Does it match the expected tone?
        2. Clarity: Is the message clear and well-structured?
        3. Grammar: Are there any grammatical errors?
        4. Completeness: Does it cover all necessary points?
        5. Professional Quality: Is it polished and professional?
        
        If the email needs improvement, provide an improved version.
        If it's already excellent, return it as-is.
        
        Return ONLY the final email draft (improved or original), no explanations.
        """)
    
    def review(self, draft: str, tone: str, intent: str) -> Dict:
        """
        Review and improve email draft.
        
        Args:
            draft: Email draft to review
            tone: Expected tone of the email
            intent: Email intent classification
            
        Returns:
            Dict: Review result with approved status, final draft, and any issues found
        """
        try:
            # First do quick validation checks
            issues = self._quick_validation(draft)
            
            # If no issues found, consider it approved
            if not issues:
                return {
                    "approved": True,
                    "final_draft": draft,
                    "issues": [],
                    "improved": False
                }
            
            # Use LLM to review and improve
            chain = self.review_prompt | self.llm
            response = self.llm_wrapper.invoke_chain(chain, {
                "draft": draft,
                "tone": tone,
                "intent": intent
            })
            
            improved_draft = response.content.strip()
            
            return {
                "approved": True,
                "final_draft": improved_draft,
                "issues": issues,
                "improved": True
            }
            
        except Exception as e:
            print(f"Error reviewing draft: {e}")
            # Return original draft if review fails
            return {
                "approved": True,
                "final_draft": draft,
                "issues": ["Review service temporarily unavailable"],
                "improved": False
            }
    
    def _quick_validation(self, draft: str) -> List[str]:
        """
        Quick validation checks on draft.
        
        Checks:
        - Minimum length
        - Presence of greeting
        - Presence of closing
        - Excessive punctuation
        
        Args:
            draft: Email draft to validate
            
        Returns:
            List[str]: List of validation issues found (empty if none)
        """
        issues = []
        
        # Check minimum length (30 words)
        word_count = len(draft.split())
        if word_count < 30:
            issues.append(f"Email too short ({word_count} words, minimum 30 recommended)")
        
        # Check for greeting
        greetings = ["dear", "hi", "hello", "hey"]
        has_greeting = any(g in draft.lower()[:100] for g in greetings)
        if not has_greeting:
            issues.append("Missing greeting (Dear, Hi, Hello, Hey)")
        
        # Check for closing
        closings = ["regards", "sincerely", "best", "thanks", "cheers", "respectfully"]
        has_closing = any(c in draft.lower()[-150:] for c in closings)
        if not has_closing:
            issues.append("Missing closing (Regards, Sincerely, Best, etc.)")
        
        # Check for excessive exclamation marks
        exclamation_count = draft.count("!")
        if exclamation_count > 3:
            issues.append(f"Too many exclamation marks ({exclamation_count}, max 3 recommended)")
        
        # Check for excessive question marks
        question_count = draft.count("?")
        if question_count > 5:
            issues.append(f"Too many question marks ({question_count}, max 5 recommended)")
        
        return issues
    
    def __call__(self, state: Dict) -> Dict:
        """
        LangGraph node function - processes state and returns updates.
        
        Args:
            state: Current workflow state with draft, tone, and intent
            
        Returns:
            Dict: Updated state with final draft and metadata
        """
        # Use personalized_draft if available, otherwise use draft
        draft_to_review = state.get("personalized_draft", state.get("draft", ""))
        
        result = self.review(
            draft_to_review,
            state.get("tone", "formal"),
            state.get("intent", "outreach")
        )
        
        return {
            "final_draft": result["final_draft"],
            "metadata": {
                "approved": result["approved"],
                "issues": result.get("issues", []),
                "improved": result.get("improved", False)
            }
        }
