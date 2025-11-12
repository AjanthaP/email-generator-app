"""
Authentication Manager - Main authentication interface.

Combines UserManager and SessionManager to provide complete authentication flow.
"""

from typing import Dict, Optional
from .user_manager import UserManager
from .session_manager import SessionManager


class AuthManager:
    """
    Main authentication manager combining user and session management.
    
    Provides high-level authentication operations:
    - User registration and login
    - Session management
    - Password management
    - Access control
    
    Example:
        >>> auth = AuthManager()
        >>> # Register new user
        >>> auth.register("user@example.com", "SecurePass123", "John Doe")
        >>> # Login
        >>> result = auth.login("user@example.com", "SecurePass123")
        >>> token = result["token"]
        >>> # Verify session
        >>> if auth.is_authenticated(token):
        ...     user = auth.get_current_user(token)
    """
    
    def __init__(
        self,
        users_file: str = "data/users/users.json",
        sessions_file: str = "data/sessions/sessions.json",
        session_duration_hours: int = 24
    ):
        """
        Initialize Authentication Manager.
        
        Args:
            users_file: Path to users data file
            sessions_file: Path to sessions data file
            session_duration_hours: Session expiration time in hours
        """
        self.user_manager = UserManager(users_file)
        self.session_manager = SessionManager(sessions_file, session_duration_hours)
    
    def register(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str = "user",
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Register a new user.
        
        Args:
            email: User's email address
            password: Plain text password
            full_name: User's full name
            role: User role (user, admin)
            metadata: Additional metadata
            
        Returns:
            Dict with registration result
        """
        try:
            result = self.user_manager.register_user(
                email=email,
                password=password,
                full_name=full_name,
                role=role,
                metadata=metadata
            )
            return result
        except ValueError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def login(self, email: str, password: str, remember_me: bool = False) -> Dict:
        """
        Authenticate user and create session.
        
        Args:
            email: User's email address
            password: Plain text password
            remember_me: If True, extend session duration
            
        Returns:
            Dict with login result and session token
        """
        # Verify credentials
        if not self.user_manager.verify_credentials(email, password):
            return {
                "success": False,
                "error": "Invalid email or password"
            }
        
        # Get user info
        user = self.user_manager.get_user(email)
        if not user:
            return {
                "success": False,
                "error": "User not found"
            }
        
        # Create session
        token = self.session_manager.create_session(
            email=user["email"],
            user_id=user["user_id"],
            metadata={"remember_me": remember_me}
        )
        
        return {
            "success": True,
            "token": token,
            "user": user,
            "message": "Login successful"
        }
    
    def logout(self, token: str) -> Dict:
        """
        Logout user by deleting session.
        
        Args:
            token: Session token
            
        Returns:
            Dict with logout result
        """
        if self.session_manager.delete_session(token):
            return {
                "success": True,
                "message": "Logout successful"
            }
        else:
            return {
                "success": False,
                "error": "Session not found"
            }
    
    def is_authenticated(self, token: str) -> bool:
        """
        Check if session token is valid.
        
        Args:
            token: Session token
            
        Returns:
            True if authenticated, False otherwise
        """
        return self.session_manager.is_valid(token)
    
    def get_current_user(self, token: str) -> Optional[Dict]:
        """
        Get current user information from session token.
        
        Args:
            token: Session token
            
        Returns:
            User dict or None if session invalid
        """
        session = self.session_manager.get_session(token)
        if not session:
            return None
        
        # Update activity
        self.session_manager.update_activity(token)
        
        # Get user info
        user = self.user_manager.get_user_by_id(session["user_id"])
        return user
    
    def require_auth(self, token: str) -> Dict:
        """
        Require authentication - raises error if not authenticated.
        
        Args:
            token: Session token
            
        Returns:
            User dict if authenticated
            
        Raises:
            ValueError: If not authenticated
        """
        user = self.get_current_user(token)
        if not user:
            raise ValueError("Authentication required")
        return user
    
    def require_role(self, token: str, role: str) -> Dict:
        """
        Require specific role - raises error if user doesn't have role.
        
        Args:
            token: Session token
            role: Required role
            
        Returns:
            User dict if authorized
            
        Raises:
            ValueError: If not authenticated or unauthorized
        """
        user = self.require_auth(token)
        if user.get("role") != role:
            raise ValueError(f"Role '{role}' required")
        return user
    
    def change_password(
        self,
        token: str,
        old_password: str,
        new_password: str
    ) -> Dict:
        """
        Change user password.
        
        Args:
            token: Session token
            old_password: Current password
            new_password: New password
            
        Returns:
            Dict with result
        """
        user = self.get_current_user(token)
        if not user:
            return {
                "success": False,
                "error": "Not authenticated"
            }
        
        try:
            success = self.user_manager.change_password(
                email=user["email"],
                old_password=old_password,
                new_password=new_password
            )
            
            if success:
                return {
                    "success": True,
                    "message": "Password changed successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid current password"
                }
        except ValueError as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def refresh_session(self, token: str) -> Optional[str]:
        """
        Refresh session and get new token.
        
        Args:
            token: Current session token
            
        Returns:
            New session token or None if invalid
        """
        return self.session_manager.refresh_session(token)
    
    def logout_all_sessions(self, token: str) -> Dict:
        """
        Logout from all sessions (current user).
        
        Args:
            token: Session token
            
        Returns:
            Dict with result
        """
        user = self.get_current_user(token)
        if not user:
            return {
                "success": False,
                "error": "Not authenticated"
            }
        
        count = self.session_manager.delete_user_sessions(user["user_id"])
        
        return {
            "success": True,
            "sessions_deleted": count,
            "message": f"Logged out from {count} session(s)"
        }
    
    def get_user_profile(self, token: str) -> Optional[Dict]:
        """
        Get user profile (alias for get_current_user).
        
        Args:
            token: Session token
            
        Returns:
            User dict or None
        """
        return self.get_current_user(token)
    
    def update_profile(self, token: str, updates: Dict) -> Dict:
        """
        Update user profile.
        
        Args:
            token: Session token
            updates: Dict of fields to update
            
        Returns:
            Dict with result
        """
        user = self.get_current_user(token)
        if not user:
            return {
                "success": False,
                "error": "Not authenticated"
            }
        
        if self.user_manager.update_user(user["email"], updates):
            return {
                "success": True,
                "message": "Profile updated successfully"
            }
        else:
            return {
                "success": False,
                "error": "Failed to update profile"
            }
    
    def delete_account(self, token: str, password: str) -> Dict:
        """
        Delete user account (requires password confirmation).
        
        Args:
            token: Session token
            password: Password for confirmation
            
        Returns:
            Dict with result
        """
        user = self.get_current_user(token)
        if not user:
            return {
                "success": False,
                "error": "Not authenticated"
            }
        
        # Verify password
        if not self.user_manager.verify_credentials(user["email"], password):
            return {
                "success": False,
                "error": "Invalid password"
            }
        
        # Delete all sessions
        self.session_manager.delete_user_sessions(user["user_id"])
        
        # Delete account
        if self.user_manager.delete_user(user["email"]):
            return {
                "success": True,
                "message": "Account deleted successfully"
            }
        else:
            return {
                "success": False,
                "error": "Failed to delete account"
            }
    
    def cleanup_sessions(self):
        """Cleanup expired sessions."""
        self.session_manager.cleanup()
    
    def get_stats(self) -> Dict:
        """
        Get authentication statistics.
        
        Returns:
            Dict with stats
        """
        total_users = len(self.user_manager.list_users(status="active"))
        session_stats = self.session_manager.get_session_stats()
        
        return {
            "total_active_users": total_users,
            **session_stats
        }
