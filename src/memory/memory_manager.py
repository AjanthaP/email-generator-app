"""Memory manager for saving and loading drafts and user profiles."""
import json
import os
from typing import Any, Dict, Optional
from pathlib import Path


class MemoryManager:
    """Simple memory manager using JSON files for persistence.

    Added compatibility helpers (get_draft_history, learn_from_edits) so the
    Streamlit UI and v2 guide examples that expect those methods function
    without needing the earlier, more elaborate implementation.
    """

    def __init__(self, data_dir: str = "data"):
        """Initialize the memory manager with a data directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.drafts_dir = self.data_dir / "drafts"
        self.drafts_dir.mkdir(exist_ok=True)

        self.profiles_dir = self.data_dir / "profiles"
        self.profiles_dir.mkdir(exist_ok=True)

    def save_draft(self, user_id: str, draft_data: Dict[str, Any]) -> None:
        """Save a draft to the user's draft history file."""
        user_drafts_file = self.drafts_dir / f"{user_id}_drafts.json"

        drafts = []
        if user_drafts_file.exists():
            try:
                with open(user_drafts_file, "r") as f:
                    drafts = json.load(f)
            except (json.JSONDecodeError, IOError):
                drafts = []

        drafts.append(draft_data)

        with open(user_drafts_file, "w") as f:
            json.dump(drafts, f, indent=2)

    def load_drafts(self, user_id: str) -> list[Dict[str, Any]]:
        """Load all drafts for a user."""
        user_drafts_file = self.drafts_dir / f"{user_id}_drafts.json"

        if not user_drafts_file.exists():
            return []

        try:
            with open(user_drafts_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    # --- Compatibility / Extended API ---
    def get_draft_history(self, user_id: str, limit: int = 20) -> list[Dict[str, Any]]:
        """Return recent draft history (most recent first) limited to `limit` entries.

        This mirrors the earlier guide's interface used by the Streamlit UI.
        """
        drafts = self.load_drafts(user_id)
        if not drafts:
            return []
        # Assume drafts were appended chronologically; reverse for most recent first
        return drafts[::-1][:limit]

    def learn_from_edits(self, user_id: str, original: str, edited: str) -> None:
        """Lightweight placeholder to record simple edit-derived preferences.

        Currently just stores last edit length and tone heuristic in the user's profile.
        """
        profile = self.load_profile(user_id) or {}
        prefs = profile.get("learned_preferences", {})

        # Length preference
        prefs["preferred_length"] = len(edited.split())

        # Tone heuristic based on greeting/emojis/exclamation usage
        casual_markers = ["hey", "hi", "thanks", "!"]
        formal_markers = ["dear", "sincerely", "regards", "respectfully"]
        casual_score = sum(1 for m in casual_markers if m in edited.lower())
        formal_score = sum(1 for m in formal_markers if m in edited.lower())
        if casual_score > formal_score:
            prefs["tone_preference"] = "casual"
        elif formal_score > casual_score:
            prefs["tone_preference"] = "formal"

        profile["learned_preferences"] = prefs
        # Persist updated profile (retain other fields if any)
        if profile:
            self.save_profile(user_id, profile)

    def save_profile(self, user_id: str, profile_data: Dict[str, Any]) -> None:
        """Save a user profile."""
        user_profile_file = self.profiles_dir / f"{user_id}_profile.json"

        with open(user_profile_file, "w") as f:
            json.dump(profile_data, f, indent=2)

    def load_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load a user profile."""
        user_profile_file = self.profiles_dir / f"{user_id}_profile.json"

        if not user_profile_file.exists():
            return None

        try:
            with open(user_profile_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
