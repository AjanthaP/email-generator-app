"""Quick script to check drafts for a user (diagnostics).

Run locally to verify whether drafts are being loaded from DB or JSON fallback.

Usage:
    python scripts/diagnostics/check_drafts.py <user_id>
"""
import sys
from src.memory.memory_manager import MemoryManager

def main():
    user_id = sys.argv[1] if len(sys.argv) > 1 else "ajantha22ma_gmail_com"
    mm = MemoryManager()
    drafts = mm.load_drafts(user_id)
    print(f"Found {len(drafts)} drafts for user {user_id}")

    if drafts:
        for i, d in enumerate(drafts[:5], 1):
            content = d.get("content") or d.get("draft", "")
            timestamp = d.get("created_at", "no timestamp")
            print(f"\n{i}. Created: {timestamp}")
            print(f"   Content: {content[:80]}...")
            print(f"   Metadata: {d.get('metadata', {})}")
    else:
        print("\nNo drafts found. Checking persistence backend...")
        print(f"Using DB: {mm._use_db}")
        if mm._use_db:
            print("DB connection is active - user may have no drafts yet.")
        else:
            print("Falling back to JSON files (data/drafts/). Consider setting DATABASE_URL.")

if __name__ == "__main__":
    main()
