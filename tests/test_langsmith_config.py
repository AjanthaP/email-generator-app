"""Simple LangSmith tracing test - verifies configuration without API calls."""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from utils.observability import activate_langsmith
from utils.config import settings

print("=" * 60)
print("LangSmith Configuration Test")
print("=" * 60)

# Check settings
print(f"\n✓ ENABLE_LANGSMITH: {settings.enable_langsmith}")
print(f"✓ LANGCHAIN_PROJECT: {settings.langchain_project}")
print(f"✓ LANGSMITH_API_KEY: {settings.langsmith_api_key[:20]}..." if settings.langsmith_api_key else "✗ No API key")

# Check workspace ID
if hasattr(settings, 'langsmith_workspace_id') and settings.langsmith_workspace_id:
    if settings.langsmith_workspace_id == "your_workspace_id_here":
        print(f"✓ WORKSPACE_ID: Not set (using personal API key)")
    else:
        print(f"✓ WORKSPACE_ID: {settings.langsmith_workspace_id}")
else:
    print(f"✓ WORKSPACE_ID: Not set (using personal API key)")

# Activate tracing
print("\nActivating LangSmith tracing...")
success = activate_langsmith()

if success:
    print("✓ Activation successful!")
    print("\nEnvironment variables set:")
    print(f"  LANGCHAIN_TRACING_V2: {os.environ.get('LANGCHAIN_TRACING_V2')}")
    print(f"  LANGCHAIN_PROJECT: {os.environ.get('LANGCHAIN_PROJECT')}")
    print(f"  LANGSMITH_API_KEY: {os.environ.get('LANGSMITH_API_KEY', '')[:20]}...")
    workspace_id = os.environ.get('LANGSMITH_WORKSPACE_ID')
    if workspace_id:
        print(f"  LANGSMITH_WORKSPACE_ID: {workspace_id}")
    else:
        print(f"  LANGSMITH_WORKSPACE_ID: Not set (personal API key mode)")
else:
    print("✗ Activation failed!")
    sys.exit(1)

print("\n" + "=" * 60)
print("Configuration Test Complete!")
print("=" * 60)
print("\nTo verify tracing is working:")
print("1. Generate an email via the API/frontend")
print("2. Check https://smith.langchain.com/")
print("3. Look for project: 'email-generator'")
print("=" * 60)
