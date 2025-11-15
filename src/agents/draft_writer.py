"""
Draft Writer Agent - Generates email drafts based on intent and context.

This agent is responsible for creating the initial email body. It selects
the appropriate template based on the detected intent and generates a
professional, well-structured email draft that includes all key points.
"""

from typing import Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from src.utils.prompts import (
    OUTREACH_PROMPT,
    FOLLOWUP_PROMPT,
    THANKYOU_PROMPT,
    MEETING_REQUEST_PROMPT,
    APOLOGY_PROMPT,
    INFORMATION_REQUEST_PROMPT,
    STATUS_UPDATE_PROMPT,
    INTRODUCTION_PROMPT,
    NETWORKING_PROMPT,
    COMPLAINT_PROMPT,
)
from src.utils.llm_wrapper import LLMWrapper, make_wrapper


class DraftWriterAgent:
    """
    Generates email drafts based on intent and context.
    
    This agent uses intent-specific templates to generate email drafts. Each
    intent type has its own writing guidelines to ensure the generated emails
    are appropriate for their purpose.
    
    Supported intents:
    - outreach: Initial contact emails
    - follow_up: Follow-up emails to previous communications
    - thank_you: Gratitude emails
    - meeting_request: Meeting invitation emails
    - apology: Apology emails
    - information_request: Information/help request emails
    
    Example:
        >>> llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        >>> writer = DraftWriterAgent(llm)
        >>> draft = writer.write("outreach", parsed_data, "formal")
    """
    
    def __init__(self, llm: ChatGoogleGenerativeAI, llm_wrapper: Optional[LLMWrapper] = None):
        """
        Initialize Draft Writer Agent.
        
        Args:
            llm: ChatGoogleGenerativeAI instance for processing
        """
        self.llm = llm
        self.llm_wrapper = llm_wrapper or make_wrapper(llm)
        # Shared templates imported from prompts.py
        self.intent_templates = {
            "outreach": OUTREACH_PROMPT,
            "follow_up": FOLLOWUP_PROMPT,
            "thank_you": THANKYOU_PROMPT,
            "meeting_request": MEETING_REQUEST_PROMPT,
            "apology": APOLOGY_PROMPT,
            "information_request": INFORMATION_REQUEST_PROMPT,
            "status_update": STATUS_UPDATE_PROMPT,
            "introduction": INTRODUCTION_PROMPT,
            "networking": NETWORKING_PROMPT,
            "complaint": COMPLAINT_PROMPT,
        }
    
    # Removed per-agent template builders; using shared imported templates instead
    
    def write(self, intent: str, parsed_data: Dict, tone: str = "formal") -> str:
        """
        Generate email draft based on intent.
        
        Args:
            intent: Email intent classification
            parsed_data: Parsed input data with recipient, purpose, key_points
            tone: Tone preference (formal, casual, assertive, empathetic)
            
        Returns:
            str: Generated email draft
        """
        # Stub / local mode early fallback
        from src.utils.config import settings
        if getattr(settings, "donotusegemini", False) or not hasattr(self.llm, "invoke"):
            return self._fallback_draft(parsed_data)

        try:
            # Resolve target length from parsed constraints or workflow state later
            # Prefer explicit constraint length if provided in parsed_data.constraints
            constraints = parsed_data.get("constraints", {}) if isinstance(parsed_data, dict) else {}
            requested_length = None
            if isinstance(constraints, dict):
                for k in ("length", "word_count", "max_words", "target_words"):
                    if k in constraints and isinstance(constraints[k], (int, float)):
                        requested_length = int(constraints[k])
                        break

            # Fallback to workflow-provided length_preference by reading an injected attribute (set in state before call)
            # We'll access via getattr on self for simplicity; __call__ sets self._workflow_length when invoked.
            if requested_length is None:
                requested_length = getattr(self, "_workflow_length", None)

            # Apply floor logic: if requested length < 50, use 50; if None, default 170
            if requested_length is None:
                effective_length = 170
            else:
                effective_length = 50 if requested_length < 50 else requested_length

            template = self.intent_templates.get(intent, self.intent_templates["outreach"])
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.llm
            response = self.llm_wrapper.invoke_chain(chain, {
                "recipient": parsed_data.get("recipient_name", ""),
                "purpose": parsed_data.get("email_purpose", ""),
                "key_points": "\n- ".join(parsed_data.get("key_points", [])),
                "tone": tone,
                "target_length": effective_length,
            })
            draft = response.content.strip()
            return draft

        except Exception as e:
            print(f"Error writing draft: {e}")
            return self._fallback_draft(parsed_data)
    
    def _fallback_draft(self, parsed_data: Dict) -> str:
        """
        Generate fallback draft when LLM fails.
        
        Args:
            parsed_data: Parsed input data
            
        Returns:
            str: Basic email structure
        """
        recipient = parsed_data.get('recipient_name', 'there')
        purpose = parsed_data.get('email_purpose', '')
        key_points = parsed_data.get('key_points', [])
        
        draft = f"Dear {recipient},\n\n"
        draft += f"I hope this email finds you well.\n\n"
        draft += f"{purpose}\n\n"
        
        if key_points:
            for point in key_points:
                draft += f"• {point}\n"
            draft += "\n"
        
        draft += "I look forward to hearing from you.\n\n"
        draft += "Best regards"
        
        return draft
    
    def __call__(self, state: Dict) -> Dict:
        """
        LangGraph node function - processes state and returns updates.
        
        Args:
            state: Current workflow state with intent, parsed_data, and tone
            
        Returns:
            Dict: Updated state with generated draft
        """
        # Make workflow length available to write()
        self._workflow_length = state.get("length_preference")  # type: ignore[attr-defined]
        draft = self.write(
            intent=state["intent"],
            parsed_data=state["parsed_data"],
            tone=state.get("tone", "formal")
        )
        return {"draft": draft}
