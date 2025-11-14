"""Quick DB inspection utility for Railway PostgreSQL.

Usage (PowerShell):
  $env:DATABASE_URL = "<copy from Railway>"
  python scripts\db_inspect.py

This will:
  - Connect using DATABASE_URL
  - Print available tables
  - Show counts and a few sample rows from key tables
"""

import os
import sys
from typing import List

from sqlalchemy import create_engine, text


def main() -> int:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set. Set it to your Railway Postgres URL.")
        return 1

    print("Connecting to:")
    safe = db_url
    try:
        if "://" in db_url and "@" in db_url:
            proto, rest = db_url.split("://", 1)
            auth, host = rest.split("@", 1)
            if ":" in auth:
                user, _ = auth.split(":", 1)
            else:
                user = auth
            safe = f"{proto}://{user}:***@{host}"
    except Exception:
        pass
    print(f"  {safe}")

    engine = create_engine(db_url)

    with engine.connect() as conn:
        print("\nListing tables in 'public' schema:")
        rows = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)).fetchall()
        tables: List[str] = [r[0] for r in rows]
        for t in tables:
            print(f"  - {t}")

        def show_samples(table: str, order: str = None):
            if table not in tables:
                return
            print(f"\nTable: {table}")
            cnt = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            total = cnt.scalar() or 0
            print(f"  Count: {total}")
            if total:
                q = f"SELECT * FROM {table}"
                if order:
                    q += f" ORDER BY {order} DESC"
                q += " LIMIT 5"
                rows = conn.execute(text(q)).mappings().all()
                for i, row in enumerate(rows, 1):
                    print(f"  Row {i}: {dict(row)}")

        # Show key tables if they exist
        show_samples("user_profiles", order="created_at")
        show_samples("drafts", order="created_at")
        show_samples("oauth_sessions", order="created_at")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
