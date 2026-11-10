"""
Test script to verify draft history functionality.

This script:
1. Checks if DATABASE_URL is set
2. If yes, queries Railway PostgreSQL for drafts
3. If no, checks local JSON files
4. Creates a test draft to verify save functionality
"""
from src.memory.memory_manager import MemoryManager
from src.utils.config import settings
from datetime import datetime

def main():
    user_id = "ajantha22ma_gmail_com"
    
    print("="*60)
    print("DRAFT HISTORY DIAGNOSTIC")
    print("="*60)
    
    # Check database configuration
    print(f"\nDatabase URL configured: {bool(settings.database_url)}")
    if settings.database_url:
        # Sanitize for display
        url_parts = settings.database_url.split("@")
        if len(url_parts) > 1:
            print(f"Database host: {url_parts[1].split('/')[0]}")
    
    # Initialize memory manager
    mm = MemoryManager()
    print(f"Using database: {mm._use_db}")
    
    # Load existing drafts
    print(f"\n--- Checking drafts for user: {user_id} ---")
    drafts = mm.load_drafts(user_id, limit=10)
    print(f"Found {len(drafts)} existing drafts")
    
    if drafts:
        print("\nMost recent drafts:")
        for i, draft in enumerate(drafts[:3], 1):
            content = draft.get("content") or draft.get("draft", "")
            timestamp = draft.get("created_at", "unknown")
            metadata = draft.get("metadata", {})
            print(f"\n{i}. [{timestamp}]")
            print(f"   Content preview: {content[:80]}...")
            print(f"   Intent: {metadata.get('intent', 'N/A')}")
            print(f"   Tone: {metadata.get('tone', 'N/A')}")
    
    # Create a test draft
    print(f"\n--- Creating test draft ---")
    test_draft_data = {
        "content": f"Test email generated at {datetime.utcnow().isoformat()}",
        "draft": f"Test email generated at {datetime.utcnow().isoformat()}",  # backward compat
        "metadata": {
            "intent": "test",
            "tone": "formal",
            "recipient": "test@example.com"
        },
        "original_input": "This is a test draft to verify history functionality"
    }
    
    try:
        mm.save_draft(user_id, test_draft_data)
        print("✅ Test draft saved successfully!")
        
        # Reload to verify
        updated_drafts = mm.load_drafts(user_id, limit=1)
        if updated_drafts:
            latest = updated_drafts[0]
            print(f"✅ Verified: Latest draft content = {latest.get('content', latest.get('draft', ''))[:60]}...")
        else:
            print("⚠️ Warning: Could not retrieve saved draft")
            
    except Exception as e:
        print(f"❌ Error saving test draft: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    if mm._use_db:
        print("✅ Using PostgreSQL database")
        print("   Drafts should be accessible across deployments")
    else:
        print("⚠️ Using local JSON files")
        print("   DATABASE_URL not set - running in local fallback mode")
        print("   Drafts saved locally in: data/drafts/")
    
    total_drafts = len(mm.load_drafts(user_id))
    print(f"\nTotal drafts for {user_id}: {total_drafts}")
    
    if not mm._use_db:
        print("\n💡 To use PostgreSQL:")
        print("   1. Set DATABASE_URL in .env file")
        print("   2. Or run backend on Railway where DATABASE_URL is configured")

if __name__ == "__main__":
    main()
