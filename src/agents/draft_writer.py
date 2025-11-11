"""
Draft Writer Agent - Generates email drafts based on intent and context.

This agent is responsible for creating the initial email body. It selects
the appropriate template based on the detected intent and generates a
professional, well-structured email draft that includes all key points.
"""

from typing import Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate


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
        >>> llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")
        >>> writer = DraftWriterAgent(llm)
        >>> draft = writer.write("outreach", parsed_data, "formal")
    """
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        """
        Initialize Draft Writer Agent.
        
        Args:
            llm: ChatGoogleGenerativeAI instance for processing
        """
        self.llm = llm
        self.intent_templates = {
            "outreach": self._get_outreach_prompt(),
            "follow_up": self._get_followup_prompt(),
            "thank_you": self._get_thankyou_prompt(),
            "meeting_request": self._get_meeting_prompt(),
            "apology": self._get_apology_prompt(),
            "information_request": self._get_info_request_prompt(),
            "status_update": self._get_status_update_prompt(),
            "introduction": self._get_introduction_prompt(),
            "networking": self._get_networking_prompt(),
            "complaint": self._get_complaint_prompt(),
        }
    
    def _get_outreach_prompt(self) -> str:
        """Template for outreach emails"""
        return """
        Write a professional outreach email with this structure:
        
        1. Personalized opening (reference recipient's work/company)
        2. Brief self-introduction
        3. Clear value proposition
        4. Specific ask or next step
        5. Professional closing
        
        Recipient: {recipient}
        Purpose: {purpose}
        Key Points: {key_points}
        Tone: {tone}
        
        Make it concise (150-200 words), engaging, and action-oriented.
        """
    
    def _get_followup_prompt(self) -> str:
        """Template for follow-up emails"""
        return """
        Write a follow-up email that:
        
        1. References previous interaction/email
        2. Provides context reminder
        3. Adds new value or information
        4. Includes clear call-to-action
        5. Shows respect for their time
        
        Recipient: {recipient}
        Purpose: {purpose}
        Key Points: {key_points}
        Tone: {tone}
        
        Keep it brief (100-150 words) and non-pushy.
        """
    
    def _get_thankyou_prompt(self) -> str:
        """Template for thank you emails"""
        return """
        Write a genuine thank you email that:
        
        1. Opens with sincere gratitude
        2. Specifically mentions what you're thanking them for
        3. Explains the impact or value
        4. Offers reciprocity if appropriate
        5. Warm closing
        
        Recipient: {recipient}
        Purpose: {purpose}
        Key Points: {key_points}
        Tone: {tone}
        
        Make it warm and authentic (100-150 words).
        """
    
    def _get_meeting_prompt(self) -> str:
        """Template for meeting request emails"""
        return """
        Write a meeting request email that:
        
        1. Clear subject line suggestion
        2. Brief context for the meeting
        3. Proposed agenda or topics
        4. Specific time options or scheduling link
        5. Expected duration
        
        Recipient: {recipient}
        Purpose: {purpose}
        Key Points: {key_points}
        Tone: {tone}
        
        Be respectful and organized (150-200 words).
        """
    
    def _get_apology_prompt(self) -> str:
        """Template for apology emails"""
        return """
        Write a sincere apology email that:
        
        1. Takes clear responsibility
        2. Acknowledges the impact
        3. Explains what happened (briefly, no excuses)
        4. Describes corrective action
        5. Asks for another chance
        
        Recipient: {recipient}
        Purpose: {purpose}
        Key Points: {key_points}
        Tone: empathetic and professional
        
        Be genuine and concise (150-200 words).
        """
    
    def _get_info_request_prompt(self) -> str:
        """Template for information request emails"""
        return """
        Write an information request email that:
        
        1. Polite opening
        2. Context for your request
        3. Specific questions or information needed
        4. Why you're asking them specifically
        5. Appreciation for their time
        
        Recipient: {recipient}
        Purpose: {purpose}
        Key Points: {key_points}
        Tone: {tone}
        
        Be clear and respectful (150-200 words).
        """
    
    def _get_status_update_prompt(self) -> str:
        """Template for status update emails"""
        return """
        Write a professional status update email that:
        
        1. Clear subject line or opening about the update
        2. Current status/progress summary
        3. Key accomplishments or milestones
        4. Next steps or upcoming actions
        5. Call to action if needed
        
        Recipient: {recipient}
        Purpose: {purpose}
        Key Points: {key_points}
        Tone: {tone}
        
        Be concise and structured (150-200 words).
        """
    
    def _get_introduction_prompt(self) -> str:
        """Template for introduction emails"""
        return """
        Write a professional introduction email that:
        
        1. Warm, personalized opening
        2. Brief background about yourself
        3. How you learned about or were referred to the recipient
        4. Shared interests or mutual connections
        5. Soft ask or invitation to connect
        
        Recipient: {recipient}
        Purpose: {purpose}
        Key Points: {key_points}
        Tone: {tone}
        
        Be genuine and engaging (150-200 words).
        """
    
    def _get_networking_prompt(self) -> str:
        """Template for networking emails"""
        return """
        Write a professional networking email that:
        
        1. Personalized compliment or reference
        2. Why you admire their work
        3. What you're doing and shared interests
        4. Suggested ways to stay connected
        5. Open invitation to coffee/call
        
        Recipient: {recipient}
        Purpose: {purpose}
        Key Points: {key_points}
        Tone: {tone}
        
        Be authentic and conversational (150-200 words).
        """
    
    def _get_complaint_prompt(self) -> str:
        """Template for complaint emails"""
        return """
        Write a professional complaint email that:
        
        1. Respectful, non-accusatory opening
        2. Clear description of the issue
        3. Impact or consequences
        4. Specific resolution requested
        5. Timeline and contact information
        
        Recipient: {recipient}
        Purpose: {purpose}
        Key Points: {key_points}
        Tone: assertive and professional
        
        Be firm but constructive (150-200 words).
        """
    
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
        try:
            # Get intent-specific prompt or use outreach as fallback
            template = self.intent_templates.get(intent, self.intent_templates["outreach"])
            
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.llm
            
            response = chain.invoke({
                "recipient": parsed_data.get("recipient_name", ""),
                "purpose": parsed_data.get("email_purpose", ""),
                "key_points": "\n- ".join(parsed_data.get("key_points", [])),
                "tone": tone
            })
            
            return response.content.strip()
            
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
        draft = self.write(
            intent=state["intent"],
            parsed_data=state["parsed_data"],
            tone=state.get("tone", "formal")
        )
        return {"draft": draft}
