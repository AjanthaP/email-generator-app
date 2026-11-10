"""
Intent Detector Agent - Classifies email intent from parsed input.

This agent determines what type of email the user wants to write (outreach,
follow-up, thank you, etc.) based on the email purpose and context. Intent
classification helps select the appropriate template and writing style.
"""

from typing import Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from src.utils.prompts import INTENT_DETECTOR_PROMPT
from enum import Enum
from src.utils.llm_wrapper import LLMWrapper, make_wrapper
from src.utils.llm_response import extract_response_text
import re
import logging

logger = logging.getLogger(__name__)


class EmailIntent(str, Enum):
    """Valid email intent classifications"""
    
    OUTREACH = "outreach"
    FOLLOW_UP = "follow_up"
    APOLOGY = "apology"
    INFORMATION_REQUEST = "information_request"
    THANK_YOU = "thank_you"
    MEETING_REQUEST = "meeting_request"
    STATUS_UPDATE = "status_update"
    INTRODUCTION = "introduction"
    NETWORKING = "networking"
    COMPLAINT = "complaint"
    LEAVE_REQUEST = "leave_request"
    GENERIC = "generic"


class IntentDetectorAgent:
    """
    Classifies email intent from parsed input.
    
    This agent analyzes the email purpose, key points, and context to determine
    which category (intent) the email falls into. Intent detection is crucial for:
    - Selecting the appropriate template
    - Adjusting tone appropriately
    - Personalizing content based on intent
    - Routing to specialized handlers if needed
    
    Example:
        >>> llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        >>> detector = IntentDetectorAgent(llm)
        >>> intent = detector.detect(parsed_data)
        >>> print(intent)  # "outreach", "follow_up", etc.
    """
    
    def __init__(self, llm: ChatGoogleGenerativeAI, llm_wrapper: Optional[LLMWrapper] = None):
        """
        Initialize Intent Detector Agent.
        
        Args:
            llm: ChatGoogleGenerativeAI instance for processing
        """
        self.llm = llm
        self.llm_wrapper = llm_wrapper or make_wrapper(llm)
        self.intents = [intent.value for intent in EmailIntent]
        # Use shared intent detector prompt
        self.prompt = INTENT_DETECTOR_PROMPT
    
    def detect(self, parsed_data: Dict) -> str:
        """
        Detect email intent from parsed data.
        
        Args:
            parsed_data: Parsed input data containing email_purpose, key_points, context
            
        Returns:
            str: Intent classification (e.g., "outreach", "follow_up")
        """
        # Leave requests need a dedicated template and should not become outreach.
        if self._is_leave_request(parsed_data):
            return EmailIntent.LEAVE_REQUEST.value

        # Stub / local mode: skip LLM invocation and use heuristic
        from src.utils.config import settings
        if getattr(settings, "donotusegemini", False) or not hasattr(self.llm, "invoke"):
            purpose = (parsed_data.get("email_purpose", "") or "").lower()
            # Simple heuristic mapping
            if any(k in purpose for k in ["follow", "follow-up"]):
                return "follow_up"
            if "thank" in purpose:
                return "thank_you"
            if any(k in purpose for k in ["meeting", "schedule"]):
                return "meeting_request"
            if "apolog" in purpose:
                return "apology"
            if any(k in purpose for k in ["info", "question", "help"]):
                return "information_request"
            if any(k in purpose for k in ["status", "update"]):
                return "status_update"
            return EmailIntent.GENERIC.value

        try:
            chain = self.prompt | self.llm
            response = self.llm_wrapper.invoke_chain(chain, {
                "intents": ", ".join(self.intents),
                "original_request": parsed_data.get("original_request", ""),
                "email_purpose": parsed_data.get("email_purpose", ""),
                "key_points": ", ".join(parsed_data.get("key_points", [])),
                "context": parsed_data.get("context", "")
            })

            intent = extract_response_text(response).lower().replace(" ", "_")

            # Validate intent
            if intent in self.intents:
                return intent

            # Try to find closest match
            for valid_intent in self.intents:
                if valid_intent in intent or intent in valid_intent:
                    return valid_intent

            # Unknown or unsupported requests should not be forced into outreach.
            return EmailIntent.GENERIC.value
        except Exception as e:
            logger.exception(f"Error detecting intent: {e}")
            return EmailIntent.GENERIC.value

    @staticmethod
    def _is_leave_request(parsed_data: Dict) -> bool:
        source_text = parsed_data.get("original_request", "")
        key_points = parsed_data.get("key_points", [])
        text = " ".join(
            str(value)
            for value in (
                source_text,
                parsed_data.get("email_purpose", ""),
                parsed_data.get("context", ""),
                *(key_points if isinstance(key_points, list) else []),
            )
        ).lower()
        patterns = (
            r"\b(?:sick|medical|annual|personal|vacation|maternity|paternity|parental)\s+leave\b",
            r"\b(?:request|requesting|ask|asking|apply|applying)\s+(?:for\s+)?(?:a\s+)?(?:leave|time off|day off|absence)\b",
            r"\b(?:leave|time off|day off|absence)\s+request\b",
            r"\b(?:take|need)\s+(?:a\s+)?(?:day off|time off|leave)\b",
        )
        return any(re.search(pattern, text) for pattern in patterns)
    
    def __call__(self, state: Dict) -> Dict:
        """
        LangGraph node function - processes state and returns updates.
        
        Args:
            state: Current workflow state containing 'parsed_data'
            
        Returns:
            Dict: Updated state with detected intent
        """
        parsed_data = dict(state["parsed_data"])
        parsed_data["original_request"] = state.get("user_input", "")
        intent = self.detect(parsed_data)
        return {"intent": intent}
