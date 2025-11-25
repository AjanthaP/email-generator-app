"""
Input Parser Agent - Extracts structured data from user input.

This agent is the entry point of the email generation workflow. It takes
unstructured user requests and extracts key information needed for email
generation: recipient, purpose, key points, tone preference, and constraints.
"""

from typing import Dict, Any, Optional
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from src.utils.prompts import INPUT_PARSER_PROMPT
from pydantic import BaseModel, Field, field_validator, ValidationError
import json
from src.utils.llm_wrapper import LLMWrapper, make_wrapper


class ParsedInput(BaseModel):
    """Structured output from input parser agent"""
    
    recipient_name: str = Field(description="Name or title of recipient")
    recipient_email: Optional[str] = Field(default="", description="Email address if provided")
    email_purpose: str = Field(description="Main purpose/goal of the email")
    key_points: list[str] = Field(default_factory=list, description="Key points to include")
    tone_preference: str = Field(default="formal", description="Preferred tone")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Length, formality constraints")
    context: Optional[str] = Field(default="", description="Additional context")
    
    @field_validator('recipient_email', 'context', mode='before')
    @classmethod
    def none_to_empty_string(cls, v):
        """Convert None to empty string for optional string fields."""
        return v if v is not None else ""

    @field_validator('recipient_name', mode='before')
    @classmethod
    def recipient_required(cls, v):
        """Ensure recipient_name is always a non-empty string."""
        if v is None or (isinstance(v, str) and not v.strip()):
            return "Recipient"
        return v


class InputParserAgent:
    """
    Extracts structured data from user input.
    
    This agent uses an LLM to understand user requests and extract:
    - Recipient information
    - Email purpose and intent hints
    - Key points to include
    - Tone preferences
    - Any constraints or special requirements
    - Background context
    
    Example:
        >>> llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        >>> parser = InputParserAgent(llm)
        >>> result = parser.parse("Write an outreach email to John at TechCorp...")
        >>> print(result.email_purpose)
    """
    
    def __init__(self, llm: ChatGoogleGenerativeAI, llm_wrapper: Optional[LLMWrapper] = None):
        """
        Initialize Input Parser Agent.
        
        Args:
            llm: ChatGoogleGenerativeAI instance for processing
        """
        self.llm = llm
        self.llm_wrapper = llm_wrapper or make_wrapper(llm)
        # Use shared prompt template from prompts.py
        self.prompt = INPUT_PARSER_PROMPT
    
    def parse(self, user_input: str) -> ParsedInput:
        """
        Parse user input into structured format.
        
        Args:
            user_input: User's email composition request
            
        Returns:
            ParsedInput: Structured parsing result with recipient, purpose, key points, etc.
            
        Raises:
            ValueError: If parsing fails and no fallback could be created
        """
        # Stub / local mode: skip LLM invocation entirely
        from src.utils.config import settings  # local import to avoid circulars during tests
        if getattr(settings, "donotusegemini", False) or not hasattr(self.llm, "invoke"):
            return self._fallback_parse(user_input)

        try:
            chain = self.prompt | self.llm
            response = self.llm_wrapper.invoke_chain(chain, {"user_input": user_input})

            # Extract JSON from response
            content = response.content

            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            raw = content.strip()
            parsed_data = json.loads(raw) if raw else {}

            # Heuristic: extract explicit recipient hint from prefixed lines
            try:
                recipient_hint = None
                for ln in user_input.splitlines():
                    s = ln.strip()
                    if s.lower().startswith("recipient:"):
                        recipient_hint = s.split(":", 1)[1].strip()
                        break
                    if s.lower().startswith("to:"):
                        recipient_hint = s.split(":", 1)[1].strip()
                        break
                if recipient_hint:
                    if not isinstance(parsed_data, dict):
                        parsed_data = {}
                    if not parsed_data.get("recipient_name") or str(parsed_data.get("recipient_name")).strip() in ("", "Recipient"):
                        parsed_data["recipient_name"] = recipient_hint
            except Exception:
                pass

            # Defensive sanitation before model instantiation
            if not isinstance(parsed_data, dict):
                parsed_data = {}
            if not parsed_data.get("recipient_name"):
                parsed_data["recipient_name"] = "Recipient"
            # Ensure required keys exist to minimize validation noise
            # When missing, use simple heuristics from user_input
            parsed_data.setdefault("email_purpose", user_input[:200])
            parsed_data.setdefault("key_points", [user_input] if len(user_input) < 100 else [user_input[:100]])
            parsed_data.setdefault("tone_preference", "formal")
            parsed_data.setdefault("constraints", {})
            parsed_data.setdefault("context", user_input)

            return ParsedInput(**parsed_data)

        except (json.JSONDecodeError, ValidationError) as e:
            # Log as info (not fatal) and return fallback structure
            print(f"[InputParserAgent] Parse validation error, using fallback: {e}")
            return self._fallback_parse(user_input)
    
    def _fallback_parse(self, user_input: str) -> ParsedInput:
        """
        Create fallback parse result when LLM parsing fails.
        
        Args:
            user_input: Original user input
            
        Returns:
            ParsedInput: Default structure with basic extraction
        """
        # Try to extract a recipient from prefixed lines
        recipient = "Recipient"
        try:
            for ln in user_input.splitlines():
                s = ln.strip()
                if s.lower().startswith("recipient:"):
                    recipient = s.split(":", 1)[1].strip() or "Recipient"
                    break
                if s.lower().startswith("to:"):
                    recipient = s.split(":", 1)[1].strip() or "Recipient"
                    break
        except Exception:
            recipient = "Recipient"

        return ParsedInput(
            recipient_name=recipient,
            email_purpose=user_input[:200] if len(user_input) > 200 else user_input,
            key_points=[user_input] if len(user_input) < 100 else [user_input[:100]],
            tone_preference="formal",
            context=user_input
        )
    
    def __call__(self, state: Dict) -> Dict:
        """
        LangGraph node function - processes state and returns updates.
        
        Args:
            state: Current workflow state containing 'user_input'
            
        Returns:
            Dict: Updated state with parsed data, recipient, and intent_hint
        """
        parsed = self.parse(state["user_input"])
        
        return {
            "parsed_data": parsed.model_dump(),
            "recipient": parsed.recipient_name,
            "intent_hint": parsed.email_purpose
        }
