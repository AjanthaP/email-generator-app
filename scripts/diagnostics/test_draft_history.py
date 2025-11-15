"""Diagnostic: verify draft history persistence path (DB vs JSON)."""
from datetime import datetime
from src.memory.memory_manager import MemoryManager
from src.utils.config import settings

USER_ID = "ajantha22ma_gmail_com"

def main():
    print("="*60); print("DRAFT HISTORY DIAGNOSTIC"); print("="*60)
    print(f"Database URL configured: {bool(settings.database_url)}")
    mm = MemoryManager(); print(f"Using database: {mm._use_db}")
    drafts = mm.load_drafts(USER_ID, limit=5)
    print(f"Found {len(drafts)} existing drafts")
    for i, d in enumerate(drafts, 1):
        content = (d.get("content") or d.get("draft") or "")[:60]
        print(f"{i}. {d.get('created_at','?')} :: {content}...")
    test = {
        "content": f"Test email generated at {datetime.utcnow().isoformat()}",
        "metadata": {"intent": "test", "tone": "formal"},
        "original_input": "Diagnostic test draft"
    }
    mm.save_draft(USER_ID, test)
    print("Saved test draft.")
    latest = mm.load_drafts(USER_ID, limit=1)[0]
    print(f"Latest draft preview: {(latest.get('content') or '')[:60]}...")

if __name__ == "__main__":
    main()
