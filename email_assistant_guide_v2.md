# AI-Powered Email Assistant - Complete Build Guide

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Project Structure](#project-structure)
4. [Day 1: Core System](#day-1-core-system)
5. [Day 2: Enhancement & Polish](#day-2-enhancement--polish)
6. [Agent Implementation Details](#agent-implementation-details)
7. [Testing Strategy](#testing-strategy)
8. [Deployment Checklist](#deployment-checklist)

---

## 🎯 Project Overview

**Goal:** Build a production-ready multi-agent email assistant that generates personalized, tone-aware email drafts in 2 days.

**Key Features:**
- 7 specialized agents with distinct roles
- LangGraph workflow orchestration
- Multi-tone support (formal, casual, assertive, empathetic)
- Memory/personalization system
- Streamlit web interface
- Template library
- Export functionality

**Tech Stack:**
- **LLM:** Google Gemini 2.0 Flash (free tier: 60 req/min)
- **Framework:** LangChain + LangGraph
- **UI:** Streamlit
- **Memory:** JSON files (simple & effective)
- **Python:** 3.10+

---

## 📊 Architecture Diagram

See the separate Mermaid diagram artifact for visual workflow.

**Agent Flow:**
```
User Input → Input Parser → Intent Detector → Tone Stylist → Draft Writer → Personalization → Review → Output
                                    ↓
                                Router (handles fallbacks & routing decisions)
```

**State Management:**
- LangGraph StateGraph maintains conversation context
- User profiles stored in JSON
- Draft history tracked for learning

---

## 📁 Project Structure

```
email_assistant/
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── input_parser.py      # Extracts structured data from user input
│   │   ├── intent_detector.py   # Classifies email intent
│   │   ├── tone_stylist.py      # Adjusts tone of draft
│   │   ├── draft_writer.py      # Generates email body
│   │   ├── personalization.py   # Injects user-specific data
│   │   ├── review_agent.py      # Validates and improves draft
│   │   └── router.py            # Handles routing & fallbacks
│   ├── workflow/
│   │   ├── __init__.py
│   │   └── langgraph_flow.py    # LangGraph orchestration
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── user_profiles.json   # User personalization data
│   │   └── memory_manager.py    # Memory operations
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── prompts.py           # Prompt templates
│   │   ├── config.py            # Configuration
│   │   └── validators.py        # Input validation
│   └── ui/
│       └── streamlit_app.py     # Web interface
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_workflow.py
│   └── test_integration.py
├── data/
│   └── templates/               # Pre-built email templates
│       ├── outreach.json
│       ├── followup.json
│       └── thankyou.json
├── docs/
│   └── architecture.md
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── setup.py
```

---

## 🚀 Day 1: Core System (8-10 hours)

### Hour 1-2: Project Setup

#### Step 1: Create Project Structure
```bash
# Create project directory
mkdir email_assistant
cd email_assistant

# Create all subdirectories
mkdir -p src/{agents,workflow,memory,utils,ui} tests data/templates docs

# Create __init__.py files
touch src/__init__.py
touch src/agents/__init__.py
touch src/workflow/__init__.py
touch src/memory/__init__.py
touch src/utils/__init__.py
touch tests/__init__.py
```

#### Step 2: Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate
```

#### Step 3: Create requirements.txt
```txt
# Core dependencies
langchain==0.1.0
langchain-google-genai==1.0.0
langgraph==0.0.20
google-generativeai==0.3.0

# UI
streamlit==1.29.0

# Utilities
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Optional
black==23.12.0
flake8==6.1.0
```

#### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 5: Set Up Environment Variables
Create `.env` file:
```env
# Google Gemini API
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp

# Application Settings
APP_NAME=AI Email Assistant
DEBUG=True
LOG_LEVEL=INFO

# Optional
MAX_TOKENS=1000
TEMPERATURE=0.7
```

Create `.env.example`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
APP_NAME=AI Email Assistant
DEBUG=True
```

#### Step 6: Create Config File
Create `src/utils/config.py`:
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash-exp"
    
    # Application Settings
    app_name: str = "AI Email Assistant"
    debug: bool = False
    log_level: str = "INFO"
    
    # LLM Settings
    max_tokens: int = 1000
    temperature: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

---

### Hour 2-4: Core Agents Implementation

#### Agent 1: Input Parser (`src/agents/input_parser.py`)
```python
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json

class ParsedInput(BaseModel):
    """Structured output from input parser"""
    recipient_name: str = Field(description="Name or title of recipient")
    recipient_email: str = Field(default="", description="Email address if provided")
    email_purpose: str = Field(description="Main purpose/goal of the email")
    key_points: list[str] = Field(description="Key points to include")
    tone_preference: str = Field(default="formal", description="Preferred tone")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Length, formality constraints")
    context: str = Field(default="", description="Additional context")

class InputParserAgent:
    """Extracts structured data from user input"""
    
    def __init__(self, llm):
        self.llm = llm
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
        """Parse user input into structured format"""
        try:
            chain = self.prompt | self.llm
            response = chain.invoke({"user_input": user_input})
            
            # Extract JSON from response
            content = response.content
            
            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            parsed_data = json.loads(content.strip())
            return ParsedInput(**parsed_data)
            
        except Exception as e:
            print(f"Error parsing input: {e}")
            # Return default structure
            return ParsedInput(
                recipient_name="Recipient",
                email_purpose=user_input[:100],
                key_points=[user_input],
                tone_preference="formal"
            )
    
    def __call__(self, state: Dict) -> Dict:
        """LangGraph node function"""
        parsed = self.parse(state["user_input"])
        return {
            "parsed_data": parsed.model_dump(),
            "recipient": parsed.recipient_name,
            "intent_hint": parsed.email_purpose
        }
```

#### Agent 2: Intent Detector (`src/agents/intent_detector.py`)
```python
from typing import Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from enum import Enum

class EmailIntent(str, Enum):
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

class IntentDetectorAgent:
    """Classifies email intent from parsed input"""
    
    def __init__(self, llm):
        self.llm = llm
        self.intents = [intent.value for intent in EmailIntent]
        self.prompt = ChatPromptTemplate.from_template("""
        You are an expert at classifying email intents.
        
        Based on the email purpose and context, classify the intent into ONE of these categories:
        {intents}
        
        Email Purpose: {email_purpose}
        Key Points: {key_points}
        Context: {context}
        
        Respond with ONLY the intent category name (e.g., "outreach", "follow_up", etc.).
        No explanation needed.
        """)
    
    def detect(self, parsed_data: Dict) -> str:
        """Detect email intent from parsed data"""
        try:
            chain = self.prompt | self.llm
            response = chain.invoke({
                "intents": ", ".join(self.intents),
                "email_purpose": parsed_data.get("email_purpose", ""),
                "key_points": ", ".join(parsed_data.get("key_points", [])),
                "context": parsed_data.get("context", "")
            })
            
            intent = response.content.strip().lower().replace(" ", "_")
            
            # Validate intent
            if intent in self.intents:
                return intent
            
            # Fallback to closest match
            for valid_intent in self.intents:
                if valid_intent in intent or intent in valid_intent:
                    return valid_intent
            
            return "outreach"  # Default fallback
            
        except Exception as e:
            print(f"Error detecting intent: {e}")
            return "outreach"
    
    def __call__(self, state: Dict) -> Dict:
        """LangGraph node function"""
        intent = self.detect(state["parsed_data"])
        return {"intent": intent}
```

#### Agent 3: Draft Writer (`src/agents/draft_writer.py`)
```python
from typing import Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate

class DraftWriterAgent:
    """Generates email drafts based on intent and context"""
    
    def __init__(self, llm):
        self.llm = llm
        self.intent_templates = {
            "outreach": self._get_outreach_prompt(),
            "follow_up": self._get_followup_prompt(),
            "thank_you": self._get_thankyou_prompt(),
            "meeting_request": self._get_meeting_prompt(),
            "apology": self._get_apology_prompt(),
            "information_request": self._get_info_request_prompt(),
        }
    
    def _get_outreach_prompt(self) -> str:
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
    
    def write(self, intent: str, parsed_data: Dict, tone: str = "formal") -> str:
        """Generate email draft"""
        try:
            # Get intent-specific prompt or use generic
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
        """Fallback template if LLM fails"""
        return f"""Dear {parsed_data.get('recipient_name', 'there')},

I hope this email finds you well.

{parsed_data.get('email_purpose', 'I wanted to reach out regarding our potential collaboration.')}

{chr(10).join(['- ' + point for point in parsed_data.get('key_points', [])])}

I look forward to hearing from you.

Best regards"""
    
    def __call__(self, state: Dict) -> Dict:
        """LangGraph node function"""
        draft = self.write(
            intent=state["intent"],
            parsed_data=state["parsed_data"],
            tone=state.get("tone", "formal")
        )
        return {"draft": draft}
```

---

### Hour 4-6: LangGraph Workflow

Create `src/workflow/langgraph_flow.py`:
```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
import operator

from src.agents.input_parser import InputParserAgent
from src.agents.intent_detector import IntentDetectorAgent
from src.agents.draft_writer import DraftWriterAgent
from src.utils.config import settings

class EmailState(TypedDict):
    """State for email generation workflow"""
    # Input
    user_input: str
    tone: str
    
    # Parsed data
    parsed_data: dict
    recipient: str
    intent_hint: str
    
    # Processing
    intent: str
    draft: str
    styled_draft: str
    personalized_draft: str
    
    # Output
    final_draft: str
    metadata: dict
    
    # Error handling
    error: str
    retry_count: int

def create_email_workflow():
    """Create LangGraph workflow for email generation"""
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=settings.temperature,
        max_output_tokens=settings.max_tokens
    )
    
    # Initialize agents
    input_parser = InputParserAgent(llm)
    intent_detector = IntentDetectorAgent(llm)
    draft_writer = DraftWriterAgent(llm)
    
    # Define workflow
    workflow = StateGraph(EmailState)
    
    # Add nodes
    workflow.add_node("parse_input", input_parser)
    workflow.add_node("detect_intent", intent_detector)
    workflow.add_node("write_draft", draft_writer)
    
    # Define edges
    workflow.add_edge("parse_input", "detect_intent")
    workflow.add_edge("detect_intent", "write_draft")
    workflow.add_edge("write_draft", END)
    
    # Set entry point
    workflow.set_entry_point("parse_input")
    
    return workflow.compile()

# Convenience function
def generate_email(user_input: str, tone: str = "formal") -> dict:
    """Generate email from user input"""
    workflow = create_email_workflow()
    
    initial_state = {
        "user_input": user_input,
        "tone": tone,
        "retry_count": 0
    }
    
    result = workflow.invoke(initial_state)
    return result
```

---

### Hour 6-8: Basic Streamlit UI

Create `src/ui/streamlit_app.py`:
```python
import streamlit as st
from src.workflow.langgraph_flow import generate_email
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Page config
st.set_page_config(
    page_title="AI Email Assistant",
    page_icon="✉️",
    layout="wide"
)

# Title
st.title("✉️ AI Email Assistant")
st.markdown("Generate professional, personalized emails in seconds")

# Sidebar configuration
st.sidebar.header("⚙️ Configuration")

tone = st.sidebar.selectbox(
    "Email Tone",
    ["formal", "casual", "assertive", "empathetic"],
    help="Choose the tone for your email"
)

length_pref = st.sidebar.slider(
    "Preferred Length (words)",
    min_value=50,
    max_value=500,
    value=150,
    step=50
)

# Main input area
st.header("📝 Compose Your Email")

col1, col2 = st.columns([1, 1])

with col1:
    user_prompt = st.text_area(
        "Describe your email:",
        placeholder="Example: Write a follow-up email to John Smith from TechCorp thanking him for yesterday's meeting and proposing next steps for our collaboration...",
        height=200
    )
    
    recipient = st.text_input(
        "Recipient Name (optional):",
        placeholder="John Smith"
    )
    
    generate_btn = st.button("✨ Generate Email", type="primary", use_container_width=True)

with col2:
    st.info("💡 **Tips for best results:**\n\n"
            "- Be specific about the email purpose\n"
            "- Mention key points to include\n"
            "- Specify the recipient's role or company\n"
            "- Include any relevant context")

# Generate email
if generate_btn:
    if not user_prompt:
        st.error("Please describe your email request")
    else:
        with st.spinner("🤖 Crafting your email..."):
            try:
                # Add recipient to prompt if provided
                full_prompt = user_prompt
                if recipient:
                    full_prompt = f"Recipient: {recipient}\n\n{user_prompt}"
                
                # Generate email
                result = generate_email(full_prompt, tone)
                
                # Store in session state
                st.session_state['last_draft'] = result.get('draft', '')
                st.session_state['last_metadata'] = {
                    'intent': result.get('intent', ''),
                    'recipient': result.get('recipient', recipient),
                    'tone': tone
                }
                
            except Exception as e:
                st.error(f"Error generating email: {str(e)}")
                st.info("Please check your API key and try again")

# Display result
if 'last_draft' in st.session_state:
    st.header("📧 Your Email Draft")
    
    # Show metadata
    metadata = st.session_state.get('last_metadata', {})
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Intent", metadata.get('intent', 'N/A').replace('_', ' ').title())
    with col2:
        st.metric("Tone", metadata.get('tone', 'N/A').title())
    with col3:
        st.metric("Recipient", metadata.get('recipient', 'N/A'))
    
    # Editable draft
    edited_draft = st.text_area(
        "Edit your email:",
        value=st.session_state['last_draft'],
        height=300,
        key="email_editor"
    )
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            "📥 Download as TXT",
            edited_draft,
            file_name="email_draft.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col2:
        if st.button("📋 Copy to Clipboard", use_container_width=True):
            st.code(edited_draft, language=None)
            st.success("Draft displayed above - select and copy!")
    
    with col3:
        if st.button("🔄 Generate New", use_container_width=True):
            del st.session_state['last_draft']
            st.rerun()

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using LangChain, LangGraph, and Streamlit")
```

---

## 🌟 Day 2: Enhancement & Polish (8-10 hours)

### Hour 1-2: Tone Stylist Agent

Create `src/agents/tone_stylist.py`:
```python
from typing import Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate

class ToneStylistAgent:
    """Adjusts email tone while preserving content"""
    
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
    
    def __init__(self, llm):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_template("""
        You are an expert at adjusting email tone while preserving the core message.
        
        Original Draft:
        {draft}
        
        Target Tone: {tone}
        
        Tone Guidelines:
        - Characteristics: {characteristics}
        - Vocabulary: {vocabulary}
        - Structure: {structure}
        - Greeting style: {greeting}
        - Closing style: {closing}
        
        Rewrite the email to match the target tone perfectly while:
        1. Keeping all key points and information
        2. Maintaining appropriate length
        3. Ensuring natural flow
        4. Matching the tone guidelines exactly
        
        Return ONLY the rewritten email, no explanations.
        """)
    
    def adjust_tone(self, draft: str, tone: str) -> str:
        """Adjust email tone"""
        try:
            guidelines = self.TONE_GUIDELINES.get(tone, self.TONE_GUIDELINES["formal"])
            
            chain = self.prompt | self.llm
            response = chain.invoke({
                "draft": draft,
                "tone": tone,
                **guidelines
            })
            
            return response.content.strip()
            
        except Exception as e:
            print(f"Error adjusting tone: {e}")
            return draft  # Return original if tone adjustment fails
    
    def __call__(self, state: Dict) -> Dict:
        """LangGraph node function"""
        styled_draft = self.adjust_tone(
            state["draft"],
            state.get("tone", "formal")
        )
        return {"styled_draft": styled_draft}
```

### Hour 2-3: Personalization Agent

Create `src/agents/personalization.py`:
```python
from typing import Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
import json
import os

class PersonalizationAgent:
    """Adds personalization from user profile"""
    
    def __init__(self, llm, profile_path: str = "src/memory/user_profiles.json"):
        self.llm = llm
        self.profile_path = profile_path
        self.profiles = self._load_profiles()
        
        self.prompt = ChatPromptTemplate.from_template("""
        You are personalizing an email draft with user-specific information.
        
        Original Draft:
        {draft}
        
        User Profile:
        - Name: {user_name}
        - Title: {user_title}
        - Company: {user_company}
        - Signature: {signature}
        - Writing Style Notes: {style_notes}
        
        Personalize the email by:
        1. Adding appropriate signature at the end
        2. Incorporating user's role/company if relevant to context
        3. Matching user's preferred writing style
        4. Keeping the core message intact
        
        Return ONLY the personalized email.
        """)
    
    def _load_profiles(self) -> Dict:
        """Load user profiles from JSON"""
        if os.path.exists(self.profile_path):
            with open(self.profile_path, 'r') as f:
                return json.load(f)
        return {"default": self._get_default_profile()}
    
    def _get_default_profile(self) -> Dict:
        """Default profile template"""
        return {
            "user_name": "User",
            "user_title": "",
            "user_company": "",
            "signature": "\n\nBest regards",
            "style_notes": "professional and clear",
            "preferences": {
                "use_emojis": False,
                "include_phone": False
            }
        }
    
    def get_profile(self, user_id: str = "default") -> Dict:
        """Get user profile"""
        return self.profiles.get(user_id, self._get_default_profile())
    
    def personalize(self, draft: str, user_id: str = "default") -> str:
        """Add personalization to draft"""
        try:
            profile = self.get_profile(user_id)
            
            chain = self.prompt | self.llm
            response = chain.invoke({
                "draft": draft,
                "user_name": profile.get("user_name", ""),
                "user_title": profile.get("user_title", ""),
                "user_company": profile.get("user_company", ""),
                "signature": profile.get("signature", "\n\nBest regards"),
                "style_notes": profile.get("style_notes", "professional")
            })
            
            return response.content.strip()
            
        except Exception as e:
            print(f"Error personalizing draft: {e}")
            # Add basic signature if personalization fails
            return f"{draft}\n\nBest regards"
    
    def __call__(self, state: Dict) -> Dict:
        """LangGraph node function"""
        personalized = self.personalize(
            state.get("styled_draft", state.get("draft", "")),
            state.get("user_id", "default")
        )
        return {"personalized_draft": personalized}
```

### Hour 3-4: Review Agent

Create `src/agents/review_agent.py`:
```python
from typing import Dict, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
import re

class ReviewAgent:
    """Validates and improves email drafts"""
    
    def __init__(self, llm):
        self.llm = llm
        self.review_prompt = ChatPromptTemplate.from_template("""
        You are an expert email reviewer. Analyze this email draft and improve it.
        
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
        """Review and improve draft"""
        try:
            # Quick validation checks
            issues = self._quick_validation(draft)
            
            if not issues:
                return {
                    "approved": True,
                    "final_draft": draft,
                    "issues": []
                }
            
            # Use LLM for improvement
            chain = self.review_prompt | self.llm
            response = chain.invoke({
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
            return {
                "approved": True,
                "final_draft": draft,
                "issues": ["Review service temporarily unavailable"],
                "improved": False
            }
    
    def _quick_validation(self, draft: str) -> List[str]:
        """Quick validation checks"""
        issues = []
        
        # Check minimum length
        if len(draft.split()) < 30:
            issues.append("Email may be too short")
        
        # Check for greeting
        greetings = ["dear", "hi", "hello", "hey"]
        if not any(g in draft.lower()[:50] for g in greetings):
            issues.append("Missing greeting")
        
        # Check for closing
        closings = ["regards", "sincerely", "best", "thanks", "cheers"]
        if not any(c in draft.lower()[-100:] for c in closings):
            issues.append("Missing closing")
        
        # Check for multiple exclamation marks
        if draft.count("!") > 2:
            issues.append("Too many exclamation marks")
        
        return issues
    
    def __call__(self, state: Dict) -> Dict:
        """LangGraph node function"""
        result = self.review(
            state.get("personalized_draft", state.get("draft", "")),
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
```

### Hour 4-5: Router Agent

Create `src/agents/router.py`:
```python
from typing import Dict, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate

class RouterAgent:
    """Handles workflow routing and fallbacks"""
    
    def __init__(self, llm):
        self.llm = llm
        self.max_retries = 3
        
    def route_next_step(self, state: Dict) -> Literal["continue", "retry", "fallback"]:
        """Determine next step in workflow"""
        
        # Check for errors
        if state.get("error"):
            retry_count = state.get("retry_count", 0)
            if retry_count < self.max_retries:
                return "retry"
            else:
                return "fallback"
        
        # Check if draft needs improvement
        if state.get("needs_improvement"):
            return "retry"
        
        return "continue"
    
    def create_fallback_draft(self, state: Dict) -> str:
        """Create fallback draft when LLM fails"""
        parsed = state.get("parsed_data", {})
        recipient = parsed.get("recipient_name", "there")
        purpose = parsed.get("email_purpose", "reach out")
        key_points = parsed.get("key_points", [])
        
        fallback = f"""Dear {recipient},

I hope this email finds you well.

I wanted to {purpose}.

"""
        
        if key_points:
            fallback += "\n".join([f"• {point}" for point in key_points])
            fallback += "\n\n"
        
        fallback += """I look forward to hearing from you.

Best regards"""
        
        return fallback
    
    def __call__(self, state: Dict) -> Dict:
        """LangGraph node function"""
        next_step = self.route_next_step(state)
        
        if next_step == "fallback":
            return {
                "final_draft": self.create_fallback_draft(state),
                "metadata": {
                    "fallback_used": True,
                    "reason": state.get("error", "Unknown error")
                }
            }
        
        return {"routing_decision": next_step}
```

---

### Hour 5-6: Memory Manager

Create `src/memory/memory_manager.py`:
```python
import json
import os
from typing import Dict, List, Optional
from datetime import datetime

class MemoryManager:
    """Manages user profiles and draft history"""
    
    def __init__(self, 
                 profiles_path: str = "src/memory/user_profiles.json",
                 history_path: str = "src/memory/draft_history.json"):
        self.profiles_path = profiles_path
        self.history_path = history_path
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Create memory files if they don't exist"""
        for path in [self.profiles_path, self.history_path]:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    json.dump({}, f)
    
    # Profile Management
    def get_profile(self, user_id: str = "default") -> Dict:
        """Get user profile"""
        with open(self.profiles_path, 'r') as f:
            profiles = json.load(f)
        return profiles.get(user_id, self._default_profile())
    
    def save_profile(self, user_id: str, profile_data: Dict):
        """Save user profile"""
        with open(self.profiles_path, 'r') as f:
            profiles = json.load(f)
        
        profiles[user_id] = profile_data
        
        with open(self.profiles_path, 'w') as f:
            json.dump(profiles, f, indent=2)
    
    def update_profile(self, user_id: str, updates: Dict):
        """Update specific profile fields"""
        profile = self.get_profile(user_id)
        profile.update(updates)
        self.save_profile(user_id, profile)
    
    def _default_profile(self) -> Dict:
        """Default profile template"""
        return {
            "user_name": "User",
            "user_title": "",
            "user_company": "",
            "signature": "\n\nBest regards",
            "style_notes": "professional and clear",
            "preferences": {
                "default_tone": "formal",
                "use_emojis": False,
                "preferred_length": 150
            },
            "created_at": datetime.now().isoformat()
        }
    
    # Draft History
    def save_draft(self, user_id: str, draft_data: Dict):
        """Save draft to history"""
        with open(self.history_path, 'r') as f:
            history = json.load(f)
        
        if user_id not in history:
            history[user_id] = []
        
        draft_entry = {
            "draft_id": f"draft_{len(history[user_id]) + 1}",
            "timestamp": datetime.now().isoformat(),
            **draft_data
        }
        
        history[user_id].append(draft_entry)
        
        # Keep only last 50 drafts
        history[user_id] = history[user_id][-50:]
        
        with open(self.history_path, 'w') as f:
            json.dump(history, f, indent=2)
    
    def get_draft_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent draft history"""
        with open(self.history_path, 'r') as f:
            history = json.load(f)
        
        user_history = history.get(user_id, [])
        return user_history[-limit:][::-1]  # Most recent first
    
    def learn_from_edits(self, user_id: str, original: str, edited: str):
        """Learn from user edits to improve personalization"""
        # Analyze differences
        analysis = self._analyze_edits(original, edited)
        
        # Update profile preferences
        if analysis:
            profile = self.get_profile(user_id)
            profile.setdefault("learned_preferences", {})
            profile["learned_preferences"].update(analysis)
            self.save_profile(user_id, profile)
    
    def _analyze_edits(self, original: str, edited: str) -> Dict:
        """Analyze what changed in the edit"""
        analysis = {}
        
        # Check if user made it more casual or formal
        casual_indicators = ["hey", "hi", "thanks", "cheers", "!"]
        formal_indicators = ["dear", "sincerely", "regards", "respectfully"]
        
        orig_casual = sum(1 for ind in casual_indicators if ind in original.lower())
        edit_casual = sum(1 for ind in casual_indicators if ind in edited.lower())
        
        if edit_casual > orig_casual:
            analysis["tone_preference"] = "casual"
        elif edit_casual < orig_casual:
            analysis["tone_preference"] = "formal"
        
        # Check length preference
        orig_len = len(original.split())
        edit_len = len(edited.split())
        
        if abs(edit_len - orig_len) > 20:
            analysis["preferred_length"] = edit_len
        
        return analysis
```

Create initial `src/memory/user_profiles.json`:
```json
{
  "default": {
    "user_name": "Alex Johnson",
    "user_title": "Product Manager",
    "user_company": "TechCorp",
    "signature": "\n\nBest regards,\nAlex Johnson\nProduct Manager, TechCorp",
    "style_notes": "professional and clear, prefers concise communication",
    "preferences": {
      "default_tone": "formal",
      "use_emojis": false,
      "preferred_length": 150
    }
  }
}
```

---

### Hour 6-7: Enhanced Workflow

Update `src/workflow/langgraph_flow.py`:
```python
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
import operator

from src.agents.input_parser import InputParserAgent
from src.agents.intent_detector import IntentDetectorAgent
from src.agents.draft_writer import DraftWriterAgent
from src.agents.tone_stylist import ToneStylistAgent
from src.agents.personalization import PersonalizationAgent
from src.agents.review_agent import ReviewAgent
from src.agents.router import RouterAgent
from src.utils.config import settings

class EmailState(TypedDict):
    """State for email generation workflow"""
    # Input
    user_input: str
    tone: str
    user_id: str
    
    # Parsed data
    parsed_data: dict
    recipient: str
    intent_hint: str
    
    # Processing
    intent: str
    draft: str
    styled_draft: str
    personalized_draft: str
    
    # Output
    final_draft: str
    metadata: dict
    
    # Control flow
    error: str
    retry_count: int
    needs_improvement: bool
    routing_decision: str

def create_email_workflow():
    """Create enhanced LangGraph workflow"""
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=settings.temperature,
        max_output_tokens=settings.max_tokens
    )
    
    # Initialize all agents
    input_parser = InputParserAgent(llm)
    intent_detector = IntentDetectorAgent(llm)
    draft_writer = DraftWriterAgent(llm)
    tone_stylist = ToneStylistAgent(llm)
    personalization_agent = PersonalizationAgent(llm)
    review_agent = ReviewAgent(llm)
    router = RouterAgent(llm)
    
    # Define workflow
    workflow = StateGraph(EmailState)
    
    # Add all nodes
    workflow.add_node("parse_input", input_parser)
    workflow.add_node("detect_intent", intent_detector)
    workflow.add_node("write_draft", draft_writer)
    workflow.add_node("adjust_tone", tone_stylist)
    workflow.add_node("personalize", personalization_agent)
    workflow.add_node("review", review_agent)
    workflow.add_node("route", router)
    
    # Define edges
    workflow.add_edge("parse_input", "detect_intent")
    workflow.add_edge("detect_intent", "write_draft")
    workflow.add_edge("write_draft", "adjust_tone")
    workflow.add_edge("adjust_tone", "personalize")
    workflow.add_edge("personalize", "review")
    workflow.add_edge("review", END)
    
    # Set entry point
    workflow.set_entry_point("parse_input")
    
    return workflow.compile()

def generate_email(user_input: str, tone: str = "formal", user_id: str = "default") -> dict:
    """Generate email from user input"""
    workflow = create_email_workflow()
    
    initial_state = {
        "user_input": user_input,
        "tone": tone,
        "user_id": user_id,
        "retry_count": 0,
        "needs_improvement": False
    }
    
    try:
        result = workflow.invoke(initial_state)
        return result
    except Exception as e:
        print(f"Workflow error: {e}")
        return {
            "final_draft": "An error occurred. Please try again.",
            "error": str(e)
        }
```

---

### Hour 7-8: Enhanced Streamlit UI

Update `src/ui/streamlit_app.py`:
```python
import streamlit as st
from src.workflow.langgraph_flow import generate_email
from src.memory.memory_manager import MemoryManager
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Initialize memory manager
memory = MemoryManager()

# Page config
st.set_page_config(
    page_title="AI Email Assistant",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .draft-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("✉️ AI Email Assistant")
st.markdown("Generate professional, personalized emails in seconds")

# Sidebar configuration
st.sidebar.header("⚙️ Configuration")

# User profile selection
user_id = st.sidebar.text_input("User ID", value="default", help="Your unique identifier")

# Tone selection
tone = st.sidebar.selectbox(
    "Email Tone",
    ["formal", "casual", "assertive", "empathetic"],
    help="Choose the tone for your email"
)

# Length preference
length_pref = st.sidebar.slider(
    "Preferred Length (words)",
    min_value=50,
    max_value=500,
    value=150,
    step=50
)

# Advanced settings
with st.sidebar.expander("⚙️ Advanced Settings"):
    show_metadata = st.checkbox("Show metadata", value=True)
    save_to_history = st.checkbox("Save to history", value=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["✍️ Compose", "📝 Templates", "📚 History"])

# Tab 1: Compose
with tab1:
    st.header("📝 Compose Your Email")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        user_prompt = st.text_area(
            "Describe your email:",
            placeholder="Example: Write a follow-up email to John Smith from TechCorp thanking him for yesterday's meeting and proposing next steps for our collaboration...",
            height=200,
            key="compose_prompt"
        )
        
        recipient = st.text_input(
            "Recipient Name (optional):",
            placeholder="John Smith",
            key="compose_recipient"
        )
        
        generate_btn = st.button("✨ Generate Email", type="primary", use_container_width=True)
    
    with col2:
        st.info("💡 **Tips for best results:**\n\n"
                "- Be specific about the email purpose\n"
                "- Mention key points to include\n"
                "- Specify the recipient's role or company\n"
                "- Include any relevant context\n"
                "- Try different tones to see variations")
    
    # Generate email
    if generate_btn:
        if not user_prompt:
            st.error("⚠️ Please describe your email request")
        else:
            with st.spinner("🤖 Crafting your email..."):
                try:
                    # Add recipient to prompt if provided
                    full_prompt = user_prompt
                    if recipient:
                        full_prompt = f"Recipient: {recipient}\n\n{user_prompt}"
                    
                    # Generate email
                    result = generate_email(full_prompt, tone, user_id)
                    
                    # Store in session state
                    st.session_state['last_draft'] = result.get('final_draft', result.get('draft', ''))
                    st.session_state['last_metadata'] = {
                        'intent': result.get('intent', 'N/A'),
                        'recipient': result.get('recipient', recipient),
                        'tone': tone,
                        'original_prompt': user_prompt
                    }
                    
                    # Save to history
                    if save_to_history:
                        memory.save_draft(user_id, {
                            'prompt': user_prompt,
                            'draft': st.session_state['last_draft'],
                            'tone': tone,
                            'intent': result.get('intent', 'N/A')
                        })
                    
                    st.success("✅ Email generated successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error generating email: {str(e)}")
                    st.info("Please check your API key and try again")
    
    # Display result
    if 'last_draft' in st.session_state:
        st.markdown("---")
        st.header("📧 Your Email Draft")
        
        # Show metadata
        if show_metadata:
            metadata = st.session_state.get('last_metadata', {})
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📋 Intent", metadata.get('intent', 'N/A').replace('_', ' ').title())
            with col2:
                st.metric("🎭 Tone", metadata.get('tone', 'N/A').title())
            with col3:
                st.metric("👤 Recipient", metadata.get('recipient', 'N/A'))
        
        # Editable draft
        edited_draft = st.text_area(
            "Edit your email:",
            value=st.session_state['last_draft'],
            height=300,
            key="email_editor"
        )
        
        # Character count
        word_count = len(edited_draft.split())
        char_count = len(edited_draft)
        st.caption(f"📊 {word_count} words • {char_count} characters")
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.download_button(
                "📥 Download TXT",
                edited_draft,
                file_name="email_draft.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col2:
            st.download_button(
                "📄 Download MD",
                edited_draft,
                file_name="email_draft.md",
                mime="text/markdown",
                use_container_width=True
            )
        
        with col3:
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.code(edited_draft, language=None)
                st.success("✅ Select text above to copy!")
        
        with col4:
            if st.button("🔄 Generate New", use_container_width=True):
                # Learn from edits
                if edited_draft != st.session_state['last_draft']:
                    memory.learn_from_edits(user_id, st.session_state['last_draft'], edited_draft)
                
                del st.session_state['last_draft']
                st.rerun()

# Tab 2: Templates
with tab2:
    st.header("📝 Email Templates")
    st.markdown("Quick start with pre-built templates")
    
    templates = {
        "Cold Outreach": {
            "prompt": "Write a cold outreach email to a potential client introducing our AI consulting services",
            "tone": "formal",
            "description": "Professional introduction to prospects"
        },
        "Meeting Follow-up": {
            "prompt": "Write a follow-up email after our product demo meeting, thanking them and proposing next steps",
            "tone": "formal",
            "description": "Post-meeting thank you and next steps"
        },
        "Thank You Note": {
            "prompt": "Write a thank you email for their time and valuable feedback on our product",
            "tone": "empathetic",
            "description": "Genuine gratitude expression"
        },
        "Project Update": {
            "prompt": "Write a status update email about the Q4 project progress to stakeholders",
            "tone": "formal",
            "description": "Professional status update"
        },
        "Networking": {
            "prompt": "Write a LinkedIn connection follow-up email to continue the conversation we started at the conference",
            "tone": "casual",
            "description": "Friendly professional networking"
        },
        "Apology": {
            "prompt": "Write an apology email for missing the scheduled meeting due to an emergency",
            "tone": "empathetic",
            "description": "Sincere apology and rescheduling"
        }
    }
    
    col1, col2 = st.columns(2)
    
    for idx, (template_name, template_data) in enumerate(templates.items()):
        col = col1 if idx % 2 == 0 else col2
        
        with col:
            with st.container():
                st.subheader(template_name)
                st.caption(template_data["description"])
                st.code(template_data["prompt"], language=None)
                
                if st.button(f"Use Template: {template_name}", key=f"template_{idx}"):
                    st.session_state['compose_prompt'] = template_data["prompt"]
                    st.session_state['selected_tone'] = template_data["tone"]
                    st.success(f"✅ Template loaded! Switch to Compose tab")

# Tab 3: History
with tab3:
    st.header("📚 Draft History")
    
    history = memory.get_draft_history(user_id, limit=20)
    
    if not history:
        st.info("No draft history yet. Start composing emails to see them here!")
    else:
        st.markdown(f"Showing last {len(history)} drafts")
        
        for idx, draft_entry in enumerate(history):
            with st.expander(f"📧 {draft_entry.get('intent', 'Email').title()} • {draft_entry['timestamp'][:10]}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("**Original Prompt:**")
                    st.text(draft_entry.get('prompt', 'N/A')[:200] + "...")
                    
                    st.markdown("**Generated Draft:**")
                    st.text_area(
                        "Draft",
                        value=draft_entry.get('draft', 'N/A'),
                        height=150,
                        key=f"history_{idx}",
                        disabled=True
                    )
                
                with col2:
                    st.metric("Tone", draft_entry.get('tone', 'N/A').title())
                    st.metric("Intent", draft_entry.get('intent', 'N/A').replace('_', ' ').title())
                    
                    if st.button("🔄 Regenerate", key=f"regen_{idx}"):
                        st.session_state['compose_prompt'] = draft_entry.get('prompt', '')
                        st.success("Prompt loaded! Go to Compose tab")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("Built with ❤️ using LangChain & LangGraph")
with col2:
    st.markdown("Powered by Google Gemini 2.0 Flash")
with col3:
    st.markdown("[📖 Documentation](#) • [🐛 Report Issue](#)")
```

---

## 📊 Testing Strategy

Create `tests/test_agents.py`:
```python
import pytest
from src.agents.input_parser import InputParserAgent
from src.agents.intent_detector import IntentDetectorAgent
from src.agents.draft_writer import DraftWriterAgent
from langchain_google_genai import ChatGoogleGenerativeAI
from src.utils.config import settings

@pytest.fixture
def llm():
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key
    )

class TestInputParser:
    def test_parse_basic_input(self, llm):
        agent = InputParserAgent(llm)
        result = agent.parse("Write an email to John about meeting tomorrow")
        
        assert result.recipient_name == "John"
        assert "meeting" in result.email_purpose.lower()
    
    def test_parse_with_tone(self, llm):
        agent = InputParserAgent(llm)
        result = agent.parse("Write a casual email to Sarah about the project")
        
        assert result.tone_preference in ["casual", "formal"]

class TestIntentDetector:
    def test_detect_outreach_intent(self, llm):
        agent = IntentDetectorAgent(llm)
        parsed_data = {
            "email_purpose": "introduce our services to potential client",
            "key_points": ["AI consulting", "free consultation"],
            "context": "cold outreach"
        }
        
        intent = agent.detect(parsed_data)
        assert intent == "outreach"
    
    def test_detect_followup_intent(self, llm):
        agent = IntentDetectorAgent(llm)
        parsed_data = {
            "email_purpose": "follow up on last week's meeting",
            "key_points": ["thank you", "next steps"],
            "context": "post-meeting"
        }
        
        intent = agent.detect(parsed_data)
        assert intent == "follow_up"

class TestDraftWriter:
    def test_write_outreach_draft(self, llm):
        agent = DraftWriterAgent(llm)
        parsed_data = {
            "recipient_name": "Jane Doe",
            "email_purpose": "introduce AI consulting services",
            "key_points": ["expertise in ML", "free consultation"]
        }
        
        draft = agent.write("outreach", parsed_data, "formal")
        
        assert "Jane" in draft or "Doe" in draft
        assert len(draft.split()) > 50
        assert draft.strip().endswith(("regards", "Regards", "sincerely", "Sincerely"))
```

---


## 🚀 Deployment Checklist

### Pre-Deployment Tasks

#### 1. Environment Setup
```bash
# Create .gitignore
echo "venv/
.env
__pycache__/
*.pyc
.pytest_cache/
.coverage
*.log
src/memory/*.json
!src/memory/user_profiles.json.example" > .gitignore
```

#### 2. Create README.md
```markdown
# AI-Powered Email Assistant

A sophisticated multi-agent system that generates personalized, tone-aware email drafts using LangChain, LangGraph, and Google Gemini.

## Features

- 🤖 7 Specialized Agents (Input Parser, Intent Detector, Draft Writer, Tone Stylist, Personalization, Review, Router)
- 🎭 Multi-Tone Support (Formal, Casual, Assertive, Empathetic)
- 💾 Memory & Personalization System
- 📝 Template Library
- 📊 Draft History & Learning
- 🔄 Intelligent Routing & Fallbacks
- 📥 Export to Multiple Formats


## Add on /Good to have Features

### Planned Advanced Features (to review and implement later)

- schedule_email:
    - Purpose: Schedule email sending with timezone support and persistence.
    - Core: Use `APScheduler` (BackgroundScheduler); parse natural language time with `dateparser`; store jobs in `data/scheduled_emails.json`.
    - API (proposed): `POST /emails/schedule { draft, to, subject, send_at, timezone } -> { job_id, status, scheduled_time }`.
    - Reliability: Validate time in future; handle DST; graceful retry/backoff on failure; optional dry-run mode.
    - Optional: Google Calendar integration (events + reminders) via OAuth when configured.

- analyze_tone:
    - Purpose: Provide an analysis panel with sentiment, emotion, readability, and risk flags.
    - Metrics: sentiment score (e.g., VADER), emotion hints, formality/politeness heuristics, readability (`textstat`), wordiness/jargon, risky phrases (caps/excess exclamations).
    - Output (JSON): `{ sentiment, readability, flags[], suggestions[] }` for UI badges and tips.
    - Implementation: Start with `textstat` + simple heuristics; optionally add `language-tool-python` for grammar and HuggingFace model for sentiment if desired.

- suggest_improvements:
    - Purpose: Actionable, minimal edits for grammar, clarity, conciseness, structure, and CTA strength.
    - Output: List of suggestions with ranges and diffs: `{ id, title, description, severity, start, end, replacement }`; support 1‑click apply.
    - Implementation: Use LanguageTool rules for grammar/spelling; craft concise rewrite heuristics; optionally fall back to LLM for complex rewrites; apply via string patches.
    - UX: Show improvement chips; preview diff; apply/revert individually; keep a version history.

Integration notes:
- New agents map cleanly to the current pipeline as optional branches:
    - `DraftWriter -> ToneStylist -> (analyze_tone) -> (suggest_improvements) -> Personalization -> Review`
    - `schedule_email` is a separate post‑generation action in UI/API; not a graph node.

Dependencies (to add when implementing):
- `apscheduler`, `dateparser`, `pytz` (scheduling); `textstat`, `language-tool-python` (analysis/improvements).
    - Optional: `transformers` or `vaderSentiment`; Google Calendar client if calendar sync is enabled.

Security/ops:
- Validate and rate‑limit schedule requests; persist jobs; add a watchdog on restart to restore pending jobs; log and notify on failures.


## Architecture

```
User Input → Parser → Intent Detector → Draft Writer → Tone Stylist → Personalization → Review → Output
                               ↓
                          Router (Fallbacks)
```

## Installation

### Prerequisites
- Python 3.10 or higher
- Google Gemini API key (free tier available)

### Setup Steps

1. Clone the repository
```bash
git clone <your-repo>
cd email_assistant
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

5. Run the application
```bash
streamlit run src/ui/streamlit_app.py
```
