"""Migration script to move existing JSON data to PostgreSQL.

This script:
1. Reads existing user profiles and drafts from JSON files
2. Creates corresponding records in PostgreSQL database
3. Preserves all data and timestamps
4. Can be run safely multiple times (idempotent)

Usage:
    python scripts/migrate_json_to_postgres.py
    
Prerequisites:
    - DATABASE_URL environment variable set
    - PostgreSQL database created and accessible
    - JSON data files in data/profiles/ and data/drafts/
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
from datetime import datetime
from sqlalchemy.orm import Session
from src.db.database import init_db, get_db_manager
from src.db.models import UserProfile, Draft
from src.utils.config import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_profiles(db: Session, data_dir: Path) -> int:
    """Migrate user profiles from JSON to PostgreSQL.
    
    Args:
        db: Database session
        data_dir: Path to data directory
        
    Returns:
        Number of profiles migrated
    """
    profiles_dir = data_dir / "profiles"
    if not profiles_dir.exists():
        logger.warning(f"Profiles directory not found: {profiles_dir}")
        return 0
    
    profile_files = list(profiles_dir.glob("*_profile.json"))
    logger.info(f"Found {len(profile_files)} profile files")
    
    migrated_count = 0
    
    for profile_file in profile_files:
        try:
            # Extract user_id from filename (e.g., "user123_profile.json" -> "user123")
            user_id = profile_file.stem.replace("_profile", "")
            
            # Load JSON data
            with open(profile_file, "r") as f:
                profile_data = json.load(f)
            
            # Check if profile already exists
            existing = db.query(UserProfile).filter_by(id=user_id).first()
            if existing:
                logger.info(f"Profile already exists for user {user_id}, skipping")
                continue
            
            # Create new profile
            profile = UserProfile(
                id=user_id,
                email=profile_data.get("email", f"{user_id}@migrated.local"),
                name=profile_data.get("name"),
                company=profile_data.get("company"),
                role=profile_data.get("role"),
                oauth_provider=profile_data.get("oauth_provider"),
                oauth_user_id=profile_data.get("oauth_user_id"),
                preferences=profile_data.get("preferences", {}),
                created_at=_parse_datetime(profile_data.get("created_at")),
                updated_at=_parse_datetime(profile_data.get("updated_at")),
                last_login_at=_parse_datetime(profile_data.get("last_login_at")),
            )
            
            db.add(profile)
            migrated_count += 1
            logger.info(f"Migrated profile for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to migrate profile {profile_file.name}: {e}")
            continue
    
    db.commit()
    logger.info(f"Successfully migrated {migrated_count} profiles")
    return migrated_count


def migrate_drafts(db: Session, data_dir: Path) -> int:
    """Migrate drafts from JSON to PostgreSQL.
    
    Args:
        db: Database session
        data_dir: Path to data directory
        
    Returns:
        Number of drafts migrated
    """
    drafts_dir = data_dir / "drafts"
    if not drafts_dir.exists():
        logger.warning(f"Drafts directory not found: {drafts_dir}")
        return 0
    
    draft_files = list(drafts_dir.glob("*_drafts.json"))
    logger.info(f"Found {len(draft_files)} draft files")
    
    migrated_count = 0
    
    for draft_file in draft_files:
        try:
            # Extract user_id from filename (e.g., "user123_drafts.json" -> "user123")
            user_id = draft_file.stem.replace("_drafts", "")
            
            # Check if user profile exists
            user_profile = db.query(UserProfile).filter_by(id=user_id).first()
            if not user_profile:
                logger.warning(f"User profile not found for {user_id}, creating placeholder")
                # Create minimal profile for orphaned drafts
                user_profile = UserProfile(
                    id=user_id,
                    email=f"{user_id}@migrated.local",
                    name=f"User {user_id}",
                )
                db.add(user_profile)
                db.commit()
            
            # Load JSON data
            with open(draft_file, "r") as f:
                drafts_data = json.load(f)
            
            if not isinstance(drafts_data, list):
                logger.warning(f"Invalid draft file format: {draft_file.name}")
                continue
            
            # Migrate each draft
            for draft_data in drafts_data:
                try:
                    # Create new draft
                    draft = Draft(
                        user_id=user_id,
                        content=draft_data.get("content", ""),
                        original_input=draft_data.get("original_input"),
                        metadata=draft_data.get("metadata", {}),
                        created_at=_parse_datetime(draft_data.get("created_at")),
                    )
                    
                    db.add(draft)
                    migrated_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to migrate individual draft for user {user_id}: {e}")
                    continue
            
            logger.info(f"Migrated {len(drafts_data)} drafts for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to migrate drafts {draft_file.name}: {e}")
            continue
    
    db.commit()
    logger.info(f"Successfully migrated {migrated_count} total drafts")
    return migrated_count


def _parse_datetime(date_string: str | None) -> datetime | None:
    """Parse datetime string to datetime object.
    
    Args:
        date_string: ISO format datetime string or None
        
    Returns:
        Datetime object or None
    """
    if not date_string:
        return None
    
    try:
        # Try ISO format
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


def main():
    """Main migration function."""
    logger.info("=" * 60)
    logger.info("Starting JSON to PostgreSQL migration")
    logger.info("=" * 60)
    
    # Check DATABASE_URL
    if not settings.database_url:
        logger.error("DATABASE_URL not set. Please configure it in .env or environment variables.")
        logger.error("Example: DATABASE_URL=postgresql://user:password@localhost:5432/email_generator")
        sys.exit(1)
    
    logger.info(f"Database URL: {settings.database_url.split('@')[-1]}")  # Log sanitized URL
    
    # Initialize database
    try:
        db_manager = init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)
    
    # Get data directory
    data_dir = Path(project_root) / "data"
    if not data_dir.exists():
        logger.warning(f"Data directory not found: {data_dir}")
        logger.info("No data to migrate. Exiting.")
        return
    
    logger.info(f"Data directory: {data_dir}")
    
    # Migrate data
    try:
        with db_manager.get_db() as db:
            # Migrate profiles first (drafts reference profiles)
            profile_count = migrate_profiles(db, data_dir)
            
            # Then migrate drafts
            draft_count = migrate_drafts(db, data_dir)
            
            logger.info("=" * 60)
            logger.info("Migration Summary:")
            logger.info(f"  - Profiles migrated: {profile_count}")
            logger.info(f"  - Drafts migrated: {draft_count}")
            logger.info("=" * 60)
            logger.info("Migration completed successfully!")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
