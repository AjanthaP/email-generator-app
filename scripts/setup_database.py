"""Setup database tables for Railway PostgreSQL.

This script:
1. Connects to PostgreSQL using DATABASE_URL
2. Creates all required tables (user_profiles, drafts, oauth_sessions)
3. Verifies tables were created successfully

Usage (PowerShell):
  $env:DATABASE_URL = "<copy from Railway Postgres Connect panel>"
  python scripts\setup_database.py

After running this, you'll see the tables in Railway's Data tab.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from src.db.models import Base


def main() -> int:
    """Create database tables."""
    db_url = os.environ.get("DATABASE_URL")
    
    if not db_url:
        print("❌ ERROR: DATABASE_URL not set")
        print("\nSet it in PowerShell:")
        print('  $env:DATABASE_URL = "postgresql://..."')
        print("\nGet the URL from Railway:")
        print("  Project → Postgres service → Connect → DATABASE_URL")
        return 1

    # Sanitize for display
    safe_url = db_url
    try:
        if "://" in db_url and "@" in db_url:
            proto, rest = db_url.split("://", 1)
            auth, host = rest.split("@", 1)
            user = auth.split(":")[0] if ":" in auth else auth
            safe_url = f"{proto}://{user}:***@{host}"
    except Exception:
        pass

    print(f"🔌 Connecting to: {safe_url}")
    
    try:
        engine = create_engine(db_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected! PostgreSQL version: {version[:50]}...")
        
        print("\n📋 Creating tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
        
        if tables:
            print(f"✅ Successfully created {len(tables)} table(s):")
            for table in tables:
                print(f"   - {table}")
            print("\n✨ Done! Refresh Railway's Data tab to see your tables.")
        else:
            print("⚠️  No tables found after creation. Check for errors above.")
            return 1
        
        engine.dispose()
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify DATABASE_URL is correct (copy from Railway)")
        print("  2. Ensure Postgres service is running in Railway")
        print("  3. Check if URL includes ?sslmode=require (Railway usually adds this)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
