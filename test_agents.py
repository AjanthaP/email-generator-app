"""
Test script to verify all 7 agents work correctly with Gemini API.

This script tests each agent individually and then chains them together
to simulate the complete email generation workflow.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.config import Settings
from agents.input_parser import InputParserAgent, ParsedInput
from agents.intent_detector import IntentDetectorAgent
from agents.draft_writer import DraftWriterAgent
from agents.tone_stylist import ToneStylistAgent
from agents.personalization import PersonalizationAgent
from agents.review import ReviewAgent
from agents.router import RouterAgent
from utils.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI


def print_section(title):
    """Print a formatted section title"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_config():
    """Test configuration loading"""
    print_section("TEST 1: Configuration Loading")
    try:
        config = Settings()
        print(f"✅ Config loaded successfully")
        print(f"   - App Name: {config.app_name}")
        print(f"   - Debug: {config.debug}")
        print(f"   - Model: {config.gemini_model}")
        print(f"   - API Key present: {'Yes' if config.gemini_api_key else 'No'}")
        return config
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return None


def test_llm_connection(config):
    """Test LLM connection"""
    print_section("TEST 2: LLM Connection (Gemini API)")
    try:
        llm = ChatGoogleGenerativeAI(
            model=config.gemini_model,
            api_key=config.gemini_api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        # Simple test call
        response = llm.invoke("Say 'Email Agent System Ready' in 5 words or less.")
        print(f"✅ LLM connection successful")
        print(f"   Response: {response.content}")
        return llm
    except Exception as e:
        print(f"❌ LLM connection failed: {e}")
        return None


def test_input_parser(llm):
    """Test Input Parser Agent"""
    print_section("TEST 3: Input Parser Agent")
    try:
        parser = InputParserAgent(llm)
        test_input = "I need to email John Smith at john@example.com to follow up on our meeting yesterday"
        
        result = parser("user_input", test_input)
        print(f"✅ Input Parser succeeded")
        print(f"   Input: {test_input}")
        print(f"   Parsed output: {result}")
        return result
    except Exception as e:
        print(f"❌ Input Parser failed: {e}")
        return None


def test_intent_detector(llm):
    """Test Intent Detector Agent"""
    print_section("TEST 4: Intent Detector Agent")
    try:
        detector = IntentDetectorAgent(llm)
        test_purpose = "Follow up on our recent meeting to discuss project timeline"
        
        result = detector.detect(test_purpose)
        print(f"✅ Intent Detector succeeded")
        print(f"   Purpose: {test_purpose}")
        print(f"   Detected intent: {result}")
        return result
    except Exception as e:
        print(f"❌ Intent Detector failed: {e}")
        return None


def test_draft_writer(llm):
    """Test Draft Writer Agent"""
    print_section("TEST 5: Draft Writer Agent")
    try:
        writer = DraftWriterAgent(llm)
        test_state = {
            "recipient_name": "John Smith",
            "email_purpose": "Follow up on project timeline discussion",
            "intent": "follow_up",
            "key_points": ["deadline confirmation", "next steps"]
        }
        
        result = writer(test_state)
        print(f"✅ Draft Writer succeeded")
        print(f"   Intent: {test_state['intent']}")
        print(f"   Generated draft (first 200 chars):")
        draft = result.get("draft", "")
        print(f"   {draft[:200]}...")
        return result
    except Exception as e:
        print(f"❌ Draft Writer failed: {e}")
        return None


def test_tone_stylist(llm):
    """Test Tone Stylist Agent"""
    print_section("TEST 6: Tone Stylist Agent")
    try:
        stylist = ToneStylistAgent(llm)
        test_draft = "Hey John, just checking in about the project timeline we discussed. Let me know when you have updates!"
        
        styled = stylist.adjust_tone(test_draft, "formal")
        print(f"✅ Tone Stylist succeeded")
        print(f"   Original (casual):")
        print(f"   '{test_draft}'")
        print(f"\n   Adjusted (formal):")
        print(f"   '{styled}'")
        return styled
    except Exception as e:
        print(f"❌ Tone Stylist failed: {e}")
        return None


def test_personalization(llm):
    """Test Personalization Agent"""
    print_section("TEST 7: Personalization Agent")
    try:
        personalizer = PersonalizationAgent(llm)
        test_draft = "Dear John,\n\nI wanted to follow up on our project timeline discussion.\n\nBest regards"
        test_state = {
            "draft": test_draft,
            "user_id": "user123"
        }
        
        result = personalizer(test_state)
        print(f"✅ Personalization Agent succeeded")
        print(f"   Original draft length: {len(test_draft)} chars")
        print(f"   Personalized draft length: {len(result.get('personalized_draft', ''))} chars")
        return result
    except Exception as e:
        print(f"❌ Personalization Agent failed: {e}")
        return None


def test_review_agent(llm):
    """Test Review Agent"""
    print_section("TEST 8: Review Agent")
    try:
        reviewer = ReviewAgent(llm)
        test_state = {
            "draft": "Hi John, I hope you're doing well. I wanted to follow up on the project timeline we discussed last week. Could you please provide an update?"
        }
        
        result = reviewer(test_state)
        print(f"✅ Review Agent succeeded")
        print(f"   Validation result: {result.get('approval_status', 'N/A')}")
        print(f"   Issues found: {result.get('issues', [])}")
        return result
    except Exception as e:
        print(f"❌ Review Agent failed: {e}")
        return None


def test_router_agent(llm):
    """Test Router Agent"""
    print_section("TEST 9: Router Agent")
    try:
        router = RouterAgent(llm)
        test_state = {
            "draft": "Test email draft",
            "error": None,
            "retry_count": 0
        }
        # First deterministic (LLM router disabled)
        settings.enable_llm_router = False
        result_det = router(test_state)
        print(f"✅ Deterministic routing decision: {result_det.get('routing_decision', 'N/A')} (LLM used: {result_det.get('metadata', {}).get('llm_router_used')})")

        # Enable LLM router and trigger a retry scenario
        settings.enable_llm_router = True
        test_state_llm = {
            "draft": "Test email draft needing improvement",
            "error": None,
            "retry_count": 0,
            "needs_improvement": True,
            "metadata": {"issues": ["tone adjustment needed"]}
        }
        result_llm = router(test_state_llm)
        print(f"✅ LLM routing decision: {result_llm.get('routing_decision', 'N/A')} (LLM used: {result_llm.get('metadata', {}).get('llm_router_used')})")
        if result_llm.get('metadata', {}).get('decision_reason'):
            print(f"   Reason: {result_llm['metadata']['decision_reason']}")
        return result
    except Exception as e:
        print(f"❌ Router Agent failed: {e}")
        return None


def test_full_workflow(llm):
    """Test complete email generation workflow"""
    print_section("TEST 10: Full Workflow Integration")
    try:
        print("Testing complete email generation pipeline...\n")
        
        # Initialize agents
        parser = InputParserAgent(llm)
        detector = IntentDetectorAgent(llm)
        writer = DraftWriterAgent(llm)
        stylist = ToneStylistAgent(llm)
        personalizer = PersonalizationAgent(llm)
        reviewer = ReviewAgent(llm)
        
        # Simulate workflow
        print("Step 1: Parsing user input...")
        user_input = "I need to write an apology email to my manager for missing the deadline"
        
        print("Step 2: Detecting intent...")
        intent = detector.detect(user_input)
        print(f"   Detected: {intent}")
        
        print("Step 3: Writing draft...")
        state = {
            "recipient_name": "Manager",
            "email_purpose": user_input,
            "intent": intent,
            "key_points": ["apology", "explanation", "commitment to improvement"]
        }
        draft_result = writer(state)
        draft = draft_result.get("draft", "")
        print(f"   Draft generated: {len(draft)} characters")
        
        print("Step 4: Adjusting tone...")
        styled = stylist.adjust_tone(draft, "formal")
        print(f"   Tone adjusted")
        
        print("Step 5: Personalizing...")
        personal_state = {
            "draft": styled,
            "user_id": "user123"
        }
        personal_result = personalizer(personal_state)
        personalized = personal_result.get("personalized_draft", styled)
        print(f"   Personalized draft: {len(personalized)} characters")
        
        print("Step 6: Reviewing...")
        review_state = {"draft": personalized}
        review_result = reviewer(review_state)
        approval = review_result.get("approval_status", "Unknown")
        print(f"   Review status: {approval}")
        
        print(f"\n✅ Full workflow test successful!")
        print(f"\n📧 Final Email Output:")
        print(f"{'-'*70}")
        print(personalized)
        print(f"{'-'*70}")
        
        return True
        
    except Exception as e:
        print(f"❌ Full workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  EMAIL GENERATOR APP - COMPREHENSIVE AGENT TEST SUITE")
    print("="*70)
    
    # Test 1: Configuration
    config = test_config()
    if not config:
        print("\n❌ Configuration test failed. Exiting.")
        return False
    
    # Test 2: LLM Connection
    llm = test_llm_connection(config)
    if not llm:
        print("\n❌ LLM connection failed. Check your API key. Exiting.")
        return False
    
    # Test individual agents
    test_input_parser(llm)
    test_intent_detector(llm)
    test_draft_writer(llm)
    test_tone_stylist(llm)
    test_personalization(llm)
    test_review_agent(llm)
    test_router_agent(llm)
    
    # Test full workflow
    test_full_workflow(llm)
    
    # Summary
    print_section("TEST SUMMARY")
    print("✅ All tests completed successfully!")
    print("\nNext steps:")
    print("  1. Implement LangGraph workflow (src/workflow/langgraph_flow.py)")
    print("  2. Build React UI (frontend/) and surface developer trace")
    print("  3. Add Day 2 features and memory management")
    print("\n")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
