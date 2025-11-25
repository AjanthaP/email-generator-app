"""Quick test to verify LangSmith tracing is working.

Run this after setting ENABLE_LANGSMITH=true in .env
Then check your LangSmith dashboard at https://smith.langchain.com/
"""

from src.workflow.langgraph_flow import generate_email

print("=" * 60)
print("Testing LangSmith Tracing")
print("=" * 60)

# Generate a simple email to create a trace
result = generate_email(
    user_input="Write a brief follow-up email to Maria about the project proposal.",
    tone="formal",
    user_id="test_user",
    developer_mode=False,
    length_preference=100
)

print("\n✓ Email generated successfully!")
print(f"Final draft: {result['final_draft'][:100]}...")
print(f"\nMetadata: {result.get('metadata', {})}")

print("\n" + "=" * 60)
print("Now check LangSmith dashboard:")
print("https://smith.langchain.com/")
print(f"Project: email-generator")
print("=" * 60)
print("\nLook for a trace with tags from the workflow execution.")
print("You should see LLM calls for each agent in the pipeline.")
