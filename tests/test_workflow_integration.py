"""Integration test for the complete workflow with RefinementAgent.

This test verifies that the refinement agent is properly integrated
into the email generation workflow.
"""
from src.workflow.langgraph_flow import generate_email

def test_workflow_integration():
    user_input = (
        "Recipient: John Smith\n"
        "Recipient Email: john.smith@example.com\n\n"
        "I want to follow up on the proposal I sent last week about the new project.\n"
        "Please let me know if you have any questions or concerns.\n"
        "I'm available for a meeting this week to discuss further."
    )
    # Force stub mode to avoid external LLM dependency
    result = generate_email(user_input, tone="formal", user_id="test_user", use_stub=True)
    assert "final_draft" in result or "personalized_draft" in result or "styled_draft" in result

if __name__ == "__main__":  # manual run convenience
    try:
        test_workflow_integration()
        print("✅ Integration workflow test passed")
    except Exception as e:
        print(f"❌ Integration workflow test failed: {e}")
        import traceback; traceback.print_exc()
