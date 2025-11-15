"""Profile inspection diagnostic script.

Usage:
    python scripts/diagnostics/test_profile.py <user_id>
"""
import sys
from src.memory.memory_manager import MemoryManager

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/diagnostics/test_profile.py <user_id>")
        sys.exit(1)
    user_id = sys.argv[1].strip()
    mm = MemoryManager()
    profile = mm.load_profile(user_id)
    if profile:
        print("✅ Profile found")
        import json; print(json.dumps(profile, indent=2))
    else:
        print("❌ No profile found for that user_id")

if __name__ == "__main__":
    main()
