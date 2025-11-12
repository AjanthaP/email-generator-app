"""
Session Manager - Handles user sessions and tokens.
"""

import json
import os
import secrets
from typing import Dict, Optional
from datetime import datetime, timedelta


class SessionManager:
    """
    Manages user sessions and authentication tokens.
    
    Features:
    - Session token generation and validation
    - Session expiration management
    - Token refresh mechanism
    - Active session tracking
    - Session cleanup
    
    Example:
        >>> session_mgr = SessionManager()
        >>> token = session_mgr.create_session("user@example.com", user_id="abc123")
        >>> session = session_mgr.get_session(token)
        >>> if session_mgr.is_valid(token):
        ...     print("Session is active")
    """
    
    def __init__(
        self,
        sessions_file: str = "data/sessions/sessions.json",
        session_duration_hours: int = 24,
        token_length: int = 32
    ):
        """
        Initialize Session Manager.
        
        Args:
            sessions_file: Path to JSON file storing session data
            session_duration_hours: Session expiration time in hours
            token_length: Length of session token in bytes
        """
        self.sessions_file = sessions_file
        self.session_duration = timedelta(hours=session_duration_hours)
        self.token_length = token_length
        self.sessions: Dict[str, Dict] = {}
        self._ensure_data_dir()
        self._load_sessions()
    
    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist."""
        os.makedirs(os.path.dirname(self.sessions_file), exist_ok=True)
    
    def _load_sessions(self):
        """Load sessions from JSON file."""
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, 'r') as f:
                    self.sessions = json.load(f)
                # Clean expired sessions on load
                self._cleanup_expired_sessions()
            except (json.JSONDecodeError, FileNotFoundError):
                self.sessions = {}
    
    def _save_sessions(self):
        """Save sessions to JSON file."""
        with open(self.sessions_file, 'w') as f:
            json.dump(self.sessions, f, indent=2)
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        now = datetime.utcnow()
        expired_tokens = []
        
        for token, session in self.sessions.items():
            expires_at = datetime.fromisoformat(session["expires_at"])
            if now > expires_at:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self.sessions[token]
        
        if expired_tokens:
            self._save_sessions()
    
    def create_session(
        self,
        email: str,
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create a new session for a user.
        
        Args:
            email: User's email address
            user_id: User's unique ID
            metadata: Additional session metadata
            
        Returns:
            Session token
        """
        # Generate secure token
        token = secrets.token_urlsafe(self.token_length)
        
        # Calculate expiration
        created_at = datetime.utcnow()
        expires_at = created_at + self.session_duration
        
        # Create session record
        self.sessions[token] = {
            "token": token,
            "email": email,
            "user_id": user_id,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "last_activity": created_at.isoformat(),
            "metadata": metadata or {}
        }
        
        self._save_sessions()
        
        return token
    
    def get_session(self, token: str) -> Optional[Dict]:
        """
        Get session information by token.
        
        Args:
            token: Session token
            
        Returns:
            Session dict or None if not found/expired
        """
        if token not in self.sessions:
            return None
        
        session = self.sessions[token]
        
        # Check expiration
        expires_at = datetime.fromisoformat(session["expires_at"])
        if datetime.utcnow() > expires_at:
            self.delete_session(token)
            return None
        
        return session
    
    def is_valid(self, token: str) -> bool:
        """
        Check if session token is valid.
        
        Args:
            token: Session token
            
        Returns:
            True if valid and not expired, False otherwise
        """
        return self.get_session(token) is not None
    
    def update_activity(self, token: str) -> bool:
        """
        Update last activity timestamp for a session.
        
        Args:
            token: Session token
            
        Returns:
            True if successful, False if session not found
        """
        if token not in self.sessions:
            return False
        
        self.sessions[token]["last_activity"] = datetime.utcnow().isoformat()
        self._save_sessions()
        
        return True
    
    def refresh_session(self, token: str) -> Optional[str]:
        """
        Refresh a session (extend expiration and optionally generate new token).
        
        Args:
            token: Current session token
            
        Returns:
            New session token or None if session not found
        """
        session = self.get_session(token)
        if not session:
            return None
        
        # Delete old session
        self.delete_session(token)
        
        # Create new session
        new_token = self.create_session(
            email=session["email"],
            user_id=session["user_id"],
            metadata=session.get("metadata", {})
        )
        
        return new_token
    
    def delete_session(self, token: str) -> bool:
        """
        Delete a session (logout).
        
        Args:
            token: Session token
            
        Returns:
            True if successful, False if session not found
        """
        if token not in self.sessions:
            return False
        
        del self.sessions[token]
        self._save_sessions()
        
        return True
    
    def delete_user_sessions(self, user_id: str) -> int:
        """
        Delete all sessions for a specific user.
        
        Args:
            user_id: User's unique ID
            
        Returns:
            Number of sessions deleted
        """
        tokens_to_delete = [
            token for token, session in self.sessions.items()
            if session.get("user_id") == user_id
        ]
        
        for token in tokens_to_delete:
            del self.sessions[token]
        
        if tokens_to_delete:
            self._save_sessions()
        
        return len(tokens_to_delete)
    
    def get_user_sessions(self, user_id: str) -> list[Dict]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User's unique ID
            
        Returns:
            List of session dicts
        """
        sessions = []
        
        for token, session in self.sessions.items():
            if session.get("user_id") == user_id:
                # Check if expired
                expires_at = datetime.fromisoformat(session["expires_at"])
                if datetime.utcnow() <= expires_at:
                    sessions.append(session)
        
        return sessions
    
    def cleanup(self):
        """Manually trigger cleanup of expired sessions."""
        self._cleanup_expired_sessions()
    
    def get_session_stats(self) -> Dict:
        """
        Get session statistics.
        
        Returns:
            Dict with session stats
        """
        self._cleanup_expired_sessions()
        
        active_sessions = len(self.sessions)
        unique_users = len(set(s["user_id"] for s in self.sessions.values()))
        
        return {
            "active_sessions": active_sessions,
            "unique_users": unique_users,
            "total_sessions_ever": active_sessions  # Would need persistence for true count
        }
