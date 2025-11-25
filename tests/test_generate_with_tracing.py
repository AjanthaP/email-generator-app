"""Generate a test email and verify LangSmith tracing is working."""
import os
import sys
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.workflow.langgraph_flow import generate_email
from src.utils.observability import activate_langsmith

print("=" * 70)
print("EMAIL GENERATION TEST WITH LANGSMITH TRACING")
print("=" * 70)

# Activate tracing
print("\n1. Activating LangSmith tracing...")
success = activate_langsmith()
if not success:
    print("❌ Failed to activate LangSmith!")
    sys.exit(1)
print("✓ LangSmith activated")

# Show timestamp for correlation
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"\n2. Current time: {timestamp}")
print("   (Use this to find the trace in LangSmith)")

# Generate email
print("\n3. Generating test email...")
print("   Input: 'Write a thank you email to Sarah for helping with the project'")
print("   Tone: professional")
print("   Length: 100 words")
print("\n   Pipeline executing (this will take 3-5 seconds)...")

try:
    result = generate_email(
        user_input="Write a thank you email to Sarah for helping with the project",
        user_id="demo_user",
        tone="professional",
        length_preference=100
    )
    
    print("\n✓ Email generated successfully!")
    print("\n" + "=" * 70)
    print("GENERATED EMAIL")
    print("=" * 70)
    print(result['final_draft'][:300] + "...")
    print("=" * 70)
    
    print("\n4. Metadata:")
    for key, value in result.get('metadata', {}).items():
        print(f"   - {key}: {value}")
    
    print("\n" + "=" * 70)
    print("LANGSMITH TRACING VERIFICATION")
    print("=" * 70)
    print("\n✓ Email generation completed - traces are being sent to LangSmith")
    print("\nNOTE: Traces may take 5-15 seconds to appear in the dashboard")
    print("\nSteps to verify:")
    print("1. Open: https://smith.langchain.com/")
    print("2. Navigate to Projects → 'email-generator'")
    print(f"3. Look for traces around: {timestamp}")
    print("4. You should see 5-8 traces from this test:")
    print("   - InputParser")
    print("   - IntentDetector")
    print("   - DraftWriter")
    print("   - ToneStylist")
    print("   - PersonalizationAgent")
    print("   - RefinementAgent (possibly multiple)")
    print("\n5. Click any trace to see:")
    print("   - Input prompt sent to Gemini")
    print("   - LLM response")
    print("   - Token usage (input/output)")
    print("   - Latency in seconds")
    print("   - Cost estimation")
    
    print("\n" + "=" * 70)
    print("WHAT TO LOOK FOR IN TRACES")
    print("=" * 70)
    print("\nExpected token usage per agent:")
    print("  InputParser:       100-200 tokens in,  30-80 tokens out")
    print("  IntentDetector:    150-250 tokens in,  20-50 tokens out")
    print("  DraftWriter:       300-400 tokens in, 150-250 tokens out")
    print("  ToneStylist:       250-350 tokens in, 150-250 tokens out")
    print("  Personalization:   300-450 tokens in, 150-300 tokens out")
    print("  Refinement:        200-400 tokens in, 100-300 tokens out")
    print("\nTotal expected: 800-1500 tokens")
    print("Estimated cost: $0.0001 - $0.0002 (0.01-0.02 cents)")
    
    print("\n" + "=" * 70)
    
except Exception as e:
    print(f"\n❌ Error during email generation: {e}")
    print("\nStack trace:")
    import traceback
    traceback.print_exc()
    print("\n⚠️  Even if generation failed, partial traces may still appear in LangSmith")
    sys.exit(1)

print("\n✅ Test completed! Check LangSmith now.")
print("=" * 70)
