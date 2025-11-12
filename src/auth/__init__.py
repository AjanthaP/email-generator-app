"""
Authentication module for Email Generator App.

Provides user authentication, session management, and access control.
"""

from .auth_manager import AuthManager
from .session_manager import SessionManager
from .user_manager import UserManager

__all__ = ["AuthManager", "SessionManager", "UserManager"]
