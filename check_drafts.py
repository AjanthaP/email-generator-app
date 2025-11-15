"""Quick script to check drafts for a user."""
from src.memory.memory_manager import MemoryManager

user_id = "ajantha22ma_gmail_com"
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
    print("\nNo drafts found. Checking if database is accessible...")
    print(f"Using DB: {mm._use_db}")
    if mm._use_db:
        print("DB connection is active")
    else:
        print("Falling back to JSON files")
