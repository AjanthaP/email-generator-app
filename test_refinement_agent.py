"""
Test script for RefinementAgent.

This script tests the refinement agent with various scenarios:
1. Duplicate signatures
2. Grammar and spelling errors
3. Repetitive sentences
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from src.agents.refinement import RefinementAgent
from src.utils.config import settings

def test_duplicate_signature():
    """Test removal of duplicate signatures."""
    print("\n=== TEST 1: Duplicate Signature ===")
    
    draft = """Dear John,

I hope this email finds you well. I wanted to reach out to discuss the upcoming project and see if you would be available for a meeting next week.

I look forward to hearing from you.

Best regards,
Sarah Johnson

Best regards,
Sarah Johnson"""
    
    print("BEFORE:")
    print(draft)
    
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.3
    )
    
    agent = RefinementAgent(llm)
    refined = agent.refine(draft)
    
    print("\nAFTER:")
    print(refined)
    print("\n" + "="*50)


def test_grammar_errors():
    """Test grammar and spelling correction."""
    print("\n=== TEST 2: Grammar and Spelling Errors ===")
    
    draft = """Dear Team,

I would like too discuss about the oportunity we have. Their very interested in you're proposal and wants to move forward with the projekt.

Please let me no if your available for a meeting tommorrow.

Best regards,
Alex"""
    
    print("BEFORE:")
    print(draft)
    
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.3
    )
    
    agent = RefinementAgent(llm)
    refined = agent.refine(draft)
    
    print("\nAFTER:")
    print(refined)
    print("\n" + "="*50)


def test_repetitive_sentences():
    """Test removal of repetitive sentences."""
    print("\n=== TEST 3: Repetitive Sentences ===")
    
    draft = """Dear Maria,

I am writing to follow up on my previous email. I wanted to follow up regarding the message I sent earlier. I'm reaching out again about my earlier communication.

I hope we can schedule a meeting to discuss this further. I would like to set up a time to talk about this. Can we arrange a meeting to go over this?

Looking forward to your response.

Best regards,
Tom"""
    
    print("BEFORE:")
    print(draft)
    
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.3
    )
    
    agent = RefinementAgent(llm)
    refined = agent.refine(draft)
    
    print("\nAFTER:")
    print(refined)
    print("\n" + "="*50)


def test_combined_issues():
    """Test all issues combined."""
    print("\n=== TEST 4: Combined Issues ===")
    
    draft = """Dear Customer,

I am writing to follow up on my previous email. I wanted to follow up regarding the message I sent earlier about you're order.

Their are some issues with the shipment that we need too address. There are some problems with the delivery we need to discuss. We have some delivery issues that require attention.

Please let me no if your available for a call.

Best regards,
Customer Service Team

Best regards,
Customer Service Team"""
    
    print("BEFORE:")
    print(draft)
    
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0.3
    )
    
    agent = RefinementAgent(llm)
    refined = agent.refine(draft)
    
    print("\nAFTER:")
    print(refined)
    print("\n" + "="*50)


if __name__ == "__main__":
    print("Testing RefinementAgent...")
    print("This will test the agent's ability to:")
    print("1. Remove duplicate signatures")
    print("2. Fix grammar and spelling errors")
    print("3. Eliminate repetitive sentences")
    
    try:
        test_duplicate_signature()
        test_grammar_errors()
        test_repetitive_sentences()
        test_combined_issues()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
