"""
Input Parser Agent - Extracts structured data from user input.

This agent is the entry point of the email generation workflow. It takes
unstructured user requests and extracts key information needed for email
generation: recipient, purpose, key points, tone preference, and constraints.
"""

from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, field_validator
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
        self.prompt = ChatPromptTemplate.from_template("""
        You are an expert at understanding email composition requests.
        
        Extract the following information from the user's request:
        1. Recipient name or title
        2. Email purpose/intent
        3. Key points that must be included
        4. Tone preference (if mentioned): formal, casual, assertive, empathetic
        5. Any constraints (length, specific requirements)
        6. Additional context
        
        User Request: {user_input}
        
        Return your analysis as a JSON object with these fields:
        - recipient_name
        - recipient_email (if provided)
        - email_purpose
        - key_points (array)
        - tone_preference (default: "formal")
        - constraints (object with any limits)
        - context (any background info)
        
        Be thorough but concise. If information isn't provided, use reasonable defaults.
        """)
    
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
            
            parsed_data = json.loads(content.strip())
            return ParsedInput(**parsed_data)
            
        except (json.JSONDecodeError, ValueError) as e:
            # Log error and return fallback structure
            print(f"Error parsing input: {e}")
            return self._fallback_parse(user_input)
    
    def _fallback_parse(self, user_input: str) -> ParsedInput:
        """
        Create fallback parse result when LLM parsing fails.
        
        Args:
            user_input: Original user input
            
        Returns:
            ParsedInput: Default structure with basic extraction
        """
        return ParsedInput(
            recipient_name="Recipient",
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
