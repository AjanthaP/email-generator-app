"""Quick test to check what profile data exists for your user_id."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.memory_manager import MemoryManager

# Change this to your actual user_id (from OAuth login)
USER_ID = input("Enter your user_id (from OAuth, e.g., '108xxxxx...'): ").strip()

if not USER_ID:
    print("No user_id provided")
    sys.exit(1)

mm = MemoryManager()

print(f"\n🔍 Checking profile for user_id: {USER_ID}")
print("=" * 60)

profile = mm.load_profile(USER_ID)

if profile:
    print("✅ Profile found!")
    print(f"\nUser Name: {profile.get('user_name') or profile.get('name', 'N/A')}")
    print(f"Title: {profile.get('user_title') or profile.get('role', 'N/A')}")
    print(f"Company: {profile.get('user_company') or profile.get('company', 'N/A')}")
    print(f"Signature: {repr(profile.get('signature', 'N/A'))}")
    print(f"\nFull profile:")
    import json
    print(json.dumps(profile, indent=2))
else:
    print("❌ No profile found for this user_id")
    print("\nTroubleshooting:")
    print("  1. Make sure you've logged in via OAuth at least once")
    print("  2. Check that the user_id matches what's in localStorage")
    print("  3. Try creating the profile via the UI (Account & Profile section)")
