"""Memory manager for saving and loading drafts and user profiles."""
import json
import os
from typing import Any, Dict, Optional
from pathlib import Path


class MemoryManager:
    """Simple memory manager using JSON files for persistence."""

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
