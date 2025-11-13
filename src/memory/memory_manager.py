"""Memory manager for saving and loading drafts and user profiles.

Updated to use PostgreSQL for persistent storage in production.
Falls back to JSON files if database is not available (local dev).
"""
import json
import os
from typing import Any, Dict, Optional, List
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging

logger = logging.getLogger(__name__)


class MemoryManager:
    """Memory manager with PostgreSQL backend and JSON fallback.

    Uses PostgreSQL when available (production), falls back to JSON files
    for local development. Maintains the same API for backward compatibility.
    """

    def __init__(self, data_dir: str = "data", db_session: Session = None):
        """Initialize the memory manager.
        
        Args:
            data_dir: Directory for JSON file fallback
            db_session: Optional SQLAlchemy session for database operations
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.drafts_dir = self.data_dir / "drafts"
        self.drafts_dir.mkdir(exist_ok=True)

        self.profiles_dir = self.data_dir / "profiles"
        self.profiles_dir.mkdir(exist_ok=True)
        
        self.db_session = db_session
        self._use_db = db_session is not None
        
        if self._use_db:
            logger.info("MemoryManager initialized with PostgreSQL backend")
        else:
            logger.info("MemoryManager initialized with JSON file backend (fallback mode)")

    def _get_db(self) -> Optional[Session]:
        """Get database session, refreshing if needed."""
        if self.db_session is None:
            try:
                from src.db.database import get_db_manager
                db_manager = get_db_manager()
                return db_manager.get_session()
            except Exception as e:
                logger.warning(f"Could not get database session: {e}")
                return None
        return self.db_session

    def save_draft(self, user_id: str, draft_data: Dict[str, Any]) -> None:
        """Save a draft to the user's draft history.
        
        Args:
            user_id: User identifier
            draft_data: Draft content and metadata
                Expected keys: 'content', 'metadata' (optional), 'original_input' (optional)
        """
        if self._use_db:
            try:
                self._save_draft_db(user_id, draft_data)
                return
            except Exception as e:
                logger.error(f"Failed to save draft to database: {e}")
                logger.info("Falling back to JSON file storage")
        
        # Fallback to JSON files
        self._save_draft_json(user_id, draft_data)

    def _save_draft_db(self, user_id: str, draft_data: Dict[str, Any]) -> None:
        """Save draft to PostgreSQL database."""
        from src.db.models import Draft
        
        db = self._get_db()
        if not db:
            raise RuntimeError("Database session not available")
        
        try:
            draft = Draft(
                user_id=user_id,
                content=draft_data.get("content", ""),
                original_input=draft_data.get("original_input"),
                metadata=draft_data.get("metadata", {}),
            )
            db.add(draft)
            db.commit()
            logger.debug(f"Saved draft to database for user {user_id}")
        except Exception as e:
            db.rollback()
            raise e
        finally:
            if self.db_session is None:  # Close only if we created it
                db.close()

    def _save_draft_json(self, user_id: str, draft_data: Dict[str, Any]) -> None:
        """Save draft to JSON file (fallback)."""
        user_drafts_file = self.drafts_dir / f"{user_id}_drafts.json"

        drafts = []
        if user_drafts_file.exists():
            try:
                with open(user_drafts_file, "r") as f:
                    drafts = json.load(f)
            except (json.JSONDecodeError, IOError):
                drafts = []

        # Add timestamp if not present
        if "created_at" not in draft_data:
            draft_data["created_at"] = datetime.utcnow().isoformat()

        drafts.append(draft_data)

        with open(user_drafts_file, "w") as f:
            json.dump(drafts, f, indent=2)

    def load_drafts(self, user_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Load all drafts for a user.
        
        Args:
            user_id: User identifier
            limit: Optional limit on number of drafts to return
            
        Returns:
            List of draft dictionaries (most recent first)
        """
        if self._use_db:
            try:
                return self._load_drafts_db(user_id, limit)
            except Exception as e:
                logger.error(f"Failed to load drafts from database: {e}")
                logger.info("Falling back to JSON file storage")
        
        # Fallback to JSON files
        return self._load_drafts_json(user_id, limit)

    def _load_drafts_db(self, user_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Load drafts from PostgreSQL database."""
        from src.db.models import Draft
        
        db = self._get_db()
        if not db:
            raise RuntimeError("Database session not available")
        
        try:
            query = db.query(Draft).filter_by(user_id=user_id).order_by(desc(Draft.created_at))
            
            if limit:
                query = query.limit(limit)
            
            drafts = query.all()
            
            # Convert to dict format
            result = []
            for draft in drafts:
                result.append({
                    "id": draft.id,
                    "content": draft.content,
                    "original_input": draft.original_input,
                    "metadata": draft.metadata or {},
                    "created_at": draft.created_at.isoformat() if draft.created_at else None,
                })
            
            logger.debug(f"Loaded {len(result)} drafts from database for user {user_id}")
            return result
        finally:
            if self.db_session is None:  # Close only if we created it
                db.close()

    def _load_drafts_json(self, user_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Load drafts from JSON file (fallback)."""
        user_drafts_file = self.drafts_dir / f"{user_id}_drafts.json"

        if not user_drafts_file.exists():
            return []

        try:
            with open(user_drafts_file, "r") as f:
                drafts = json.load(f)
            
            # Return most recent first
            drafts = list(reversed(drafts))
            
            if limit:
                drafts = drafts[:limit]
            
            return drafts
        except (json.JSONDecodeError, IOError):
            return []

    def clear_drafts(self, user_id: str) -> None:
        """Remove all persisted drafts for a user.
        
        Args:
            user_id: User identifier
        """
        if self._use_db:
            try:
                self._clear_drafts_db(user_id)
                return
            except Exception as e:
                logger.error(f"Failed to clear drafts from database: {e}")
                logger.info("Falling back to JSON file storage")
        
        # Fallback to JSON files
        self._clear_drafts_json(user_id)

    def _clear_drafts_db(self, user_id: str) -> None:
        """Clear drafts from PostgreSQL database."""
        from src.db.models import Draft
        
        db = self._get_db()
        if not db:
            raise RuntimeError("Database session not available")
        
        try:
            db.query(Draft).filter_by(user_id=user_id).delete()
            db.commit()
            logger.debug(f"Cleared all drafts from database for user {user_id}")
        except Exception as e:
            db.rollback()
            raise e
        finally:
            if self.db_session is None:  # Close only if we created it
                db.close()

    def _clear_drafts_json(self, user_id: str) -> None:
        """Clear drafts from JSON file (fallback)."""
        user_drafts_file = self.drafts_dir / f"{user_id}_drafts.json"
        if user_drafts_file.exists():
            try:
                user_drafts_file.unlink()
            except OSError:
                user_drafts_file.write_text("[]", encoding="utf-8")

    # --- Compatibility / Extended API ---
    def get_draft_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Return recent draft history (most recent first).

        This mirrors the earlier guide's interface used by the Streamlit UI.
        
        Args:
            user_id: User identifier
            limit: Maximum number of drafts to return
            
        Returns:
            List of draft dictionaries (most recent first)
        """
        return self.load_drafts(user_id, limit=limit)

    def learn_from_edits(self, user_id: str, original: str, edited: str) -> None:
        """Lightweight placeholder to record simple edit-derived preferences.

        Currently just stores last edit length and tone heuristic in the user's profile.
        
        Args:
            user_id: User identifier
            original: Original draft content
            edited: User-edited content
        """
        profile = self.load_profile(user_id) or {}
        prefs = profile.get("preferences", {}) if isinstance(profile.get("preferences"), dict) else {}
        learned = prefs.get("learned_preferences", {}) if isinstance(prefs.get("learned_preferences"), dict) else {}

        # Length preference
        learned["preferred_length"] = len(edited.split())

        # Tone heuristic based on greeting/emojis/exclamation usage
        casual_markers = ["hey", "hi", "thanks", "!"]
        formal_markers = ["dear", "sincerely", "regards", "respectfully"]
        casual_score = sum(1 for m in casual_markers if m in edited.lower())
        formal_score = sum(1 for m in formal_markers if m in edited.lower())
        if casual_score > formal_score:
            learned["tone_preference"] = "casual"
        elif formal_score > casual_score:
            learned["tone_preference"] = "formal"

        prefs["learned_preferences"] = learned
        profile["preferences"] = prefs
        
        # Persist updated profile
        if profile:
            self.save_profile(user_id, profile)

    def save_profile(self, user_id: str, profile_data: Dict[str, Any]) -> None:
        """Save a user profile.
        
        Args:
            user_id: User identifier
            profile_data: Profile data dictionary
                Expected keys: 'name', 'email', 'company', 'role', 'preferences', etc.
        """
        if self._use_db:
            try:
                self._save_profile_db(user_id, profile_data)
                return
            except Exception as e:
                logger.error(f"Failed to save profile to database: {e}")
                logger.info("Falling back to JSON file storage")
        
        # Fallback to JSON files
        self._save_profile_json(user_id, profile_data)

    def _save_profile_db(self, user_id: str, profile_data: Dict[str, Any]) -> None:
        """Save profile to PostgreSQL database."""
        from src.db.models import UserProfile
        
        db = self._get_db()
        if not db:
            raise RuntimeError("Database session not available")
        
        try:
            # Check if profile exists
            profile = db.query(UserProfile).filter_by(id=user_id).first()
            
            if profile:
                # Update existing profile
                profile.name = profile_data.get("name", profile.name)
                profile.email = profile_data.get("email", profile.email)
                profile.company = profile_data.get("company", profile.company)
                profile.role = profile_data.get("role", profile.role)
                profile.oauth_provider = profile_data.get("oauth_provider", profile.oauth_provider)
                profile.oauth_user_id = profile_data.get("oauth_user_id", profile.oauth_user_id)
                profile.preferences = profile_data.get("preferences", profile.preferences)
                profile.updated_at = datetime.utcnow()
            else:
                # Create new profile
                profile = UserProfile(
                    id=user_id,
                    email=profile_data.get("email", f"{user_id}@unknown.com"),
                    name=profile_data.get("name"),
                    company=profile_data.get("company"),
                    role=profile_data.get("role"),
                    oauth_provider=profile_data.get("oauth_provider"),
                    oauth_user_id=profile_data.get("oauth_user_id"),
                    preferences=profile_data.get("preferences", {}),
                )
                db.add(profile)
            
            db.commit()
            logger.debug(f"Saved profile to database for user {user_id}")
        except Exception as e:
            db.rollback()
            raise e
        finally:
            if self.db_session is None:  # Close only if we created it
                db.close()

    def _save_profile_json(self, user_id: str, profile_data: Dict[str, Any]) -> None:
        """Save profile to JSON file (fallback)."""
        user_profile_file = self.profiles_dir / f"{user_id}_profile.json"

        with open(user_profile_file, "w") as f:
            json.dump(profile_data, f, indent=2)

    def load_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load a user profile.
        
        Args:
            user_id: User identifier
            
        Returns:
            Profile dictionary or None if not found
        """
        if self._use_db:
            try:
                return self._load_profile_db(user_id)
            except Exception as e:
                logger.error(f"Failed to load profile from database: {e}")
                logger.info("Falling back to JSON file storage")
        
        # Fallback to JSON files
        return self._load_profile_json(user_id)

    def _load_profile_db(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load profile from PostgreSQL database."""
        from src.db.models import UserProfile
        
        db = self._get_db()
        if not db:
            raise RuntimeError("Database session not available")
        
        try:
            profile = db.query(UserProfile).filter_by(id=user_id).first()
            
            if not profile:
                return None
            
            # Convert to dict format
            result = {
                "id": profile.id,
                "email": profile.email,
                "name": profile.name,
                "company": profile.company,
                "role": profile.role,
                "oauth_provider": profile.oauth_provider,
                "oauth_user_id": profile.oauth_user_id,
                "preferences": profile.preferences or {},
                "created_at": profile.created_at.isoformat() if profile.created_at else None,
                "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
                "last_login_at": profile.last_login_at.isoformat() if profile.last_login_at else None,
            }
            
            logger.debug(f"Loaded profile from database for user {user_id}")
            return result
        finally:
            if self.db_session is None:  # Close only if we created it
                db.close()

    def _load_profile_json(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load profile from JSON file (fallback)."""
        user_profile_file = self.profiles_dir / f"{user_id}_profile.json"

        if not user_profile_file.exists():
            return None

        try:
            with open(user_profile_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
