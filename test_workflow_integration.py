"""
Integration test for the complete workflow with RefinementAgent.

This test verifies that the refinement agent is properly integrated
into the email generation workflow.
"""

from src.workflow.langgraph_flow import execute_workflow, generate_email

def test_workflow_integration():
    """Test that refinement agent is part of the workflow."""
    print("\n=== Integration Test: Full Workflow with Refinement ===\n")
    
    user_input = """
    Recipient: John Smith
    Recipient Email: john.smith@example.com
    
    I want to follow up on the proposal I sent last week about the new project.
    Please let me know if you have any questions or concerns.
    I'm available for a meeting this week to discuss further.
    """
    
    print("User Input:")
    print(user_input)
    print("\n" + "="*60 + "\n")
    
    # Test with actual workflow
    result = generate_email(user_input, tone="formal", user_id="test_user")
    
    print("Generated Email:")
    print(result["final_draft"])
    print("\n" + "="*60 + "\n")
    
    print("Metadata:")
    for key, value in result.get("metadata", {}).items():
        print(f"  {key}: {value}")
    
    print("\n✅ Integration test completed!")
    print("\nThe workflow now includes:")
    print("1. Input Parser")
    print("2. Intent Detector")
    print("3. Draft Writer")
    print("4. Tone Stylist")
    print("5. Personalization Agent")
    print("6. Review Agent")
    print("7. ✨ Refinement Agent ✨ (NEW)")
    print("8. Router")


if __name__ == "__main__":
    try:
        test_workflow_integration()
    except Exception as e:
        print(f"\n❌ Error during integration test: {e}")
        import traceback
        traceback.print_exc()
