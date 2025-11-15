"""Unit tests for Authentication Module.

Run with: pytest tests/test_auth.py
"""

import pytest
import os
import json
import tempfile
from src.auth import AuthManager, UserManager, SessionManager


@pytest.fixture
def temp_dir():
    """Create temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def auth_manager(temp_dir):
    """Create AuthManager with temporary file storage."""
    users_file = os.path.join(temp_dir, "users.json")
    sessions_file = os.path.join(temp_dir, "sessions.json")
    return AuthManager(users_file=users_file, sessions_file=sessions_file)


class TestUserManager:
    """Test UserManager functionality."""

    def test_register_user(self, temp_dir):
        users_file = os.path.join(temp_dir, "users.json")
        user_mgr = UserManager(users_file)
        result = user_mgr.register_user(
            email="test@example.com", password="TestPass123", full_name="Test User"
        )
        assert result["success"] is True
        assert "user_id" in result

    def test_register_duplicate_email(self, temp_dir):
        users_file = os.path.join(temp_dir, "users.json")
        user_mgr = UserManager(users_file)
        user_mgr.register_user("test@example.com", "Pass1234", "User One")
        with pytest.raises(ValueError, match="already exists"):
            user_mgr.register_user("test@example.com", "Pass45678", "User Two")

    def test_short_password(self, temp_dir):
        users_file = os.path.join(temp_dir, "users.json")
        user_mgr = UserManager(users_file)
        with pytest.raises(ValueError, match="at least 8 characters"):
            user_mgr.register_user("test@example.com", "short", "Test User")

    def test_verify_credentials(self, temp_dir):
        users_file = os.path.join(temp_dir, "users.json")
        user_mgr = UserManager(users_file)
        user_mgr.register_user("test@example.com", "TestPass123", "Test User")
        assert user_mgr.verify_credentials("test@example.com", "TestPass123") is True
        assert user_mgr.verify_credentials("test@example.com", "WrongPass") is False
        assert user_mgr.verify_credentials("nobody@example.com", "Pass1234") is False

    def test_get_user(self, temp_dir):
        users_file = os.path.join(temp_dir, "users.json")
        user_mgr = UserManager(users_file)
        user_mgr.register_user("test@example.com", "Pass1234", "Test User")
        user = user_mgr.get_user("test@example.com")
        assert user is not None
        assert user["email"] == "test@example.com"
        assert user["full_name"] == "Test User"
        assert "password_hash" not in user
        assert "salt" not in user

    def test_change_password(self, temp_dir):
        users_file = os.path.join(temp_dir, "users.json")
        user_mgr = UserManager(users_file)
        user_mgr.register_user("test@example.com", "OldPass123", "Test User")
        success = user_mgr.change_password("test@example.com", "OldPass123", "NewPass456")
        assert success is True
        assert user_mgr.verify_credentials("test@example.com", "OldPass123") is False
        assert user_mgr.verify_credentials("test@example.com", "NewPass456") is True


class TestSessionManager:
    """Test SessionManager functionality."""
    
    def test_create_session(self, temp_dir):
        """Test session creation."""
        sessions_file = os.path.join(temp_dir, "sessions.json")
        session_mgr = SessionManager(sessions_file)
        
        token = session_mgr.create_session(
            email="test@example.com",
            user_id="user123"
        )
        
        assert token is not None
        assert len(token) > 0
    
    def test_get_session(self, temp_dir):
        """Test getting session information."""
        sessions_file = os.path.join(temp_dir, "sessions.json")
        session_mgr = SessionManager(sessions_file)
        
        token = session_mgr.create_session("test@example.com", "user123")
        session = session_mgr.get_session(token)
        
        assert session is not None
        assert session["email"] == "test@example.com"
        assert session["user_id"] == "user123"
    
    def test_is_valid(self, temp_dir):
        """Test session validation."""
        sessions_file = os.path.join(temp_dir, "sessions.json")
        session_mgr = SessionManager(sessions_file)
        
        token = session_mgr.create_session("test@example.com", "user123")
        
        assert session_mgr.is_valid(token) is True
        assert session_mgr.is_valid("invalid_token") is False
    
    def test_delete_session(self, temp_dir):
        """Test session deletion."""
        sessions_file = os.path.join(temp_dir, "sessions.json")
        session_mgr = SessionManager(sessions_file)
        
        token = session_mgr.create_session("test@example.com", "user123")
        
        assert session_mgr.is_valid(token) is True
        
        session_mgr.delete_session(token)
        
        assert session_mgr.is_valid(token) is False


class TestAuthManager:
    """Test AuthManager functionality."""
    
    def test_register(self, auth_manager):
        """Test user registration through AuthManager."""
        result = auth_manager.register(
            email="test@example.com",
            password="TestPass123",
            full_name="Test User"
        )
        
        assert result["success"] is True
        assert "user_id" in result
    
    def test_login(self, auth_manager):
        """Test login functionality."""
        # Register user
        auth_manager.register("test@example.com", "TestPass123", "Test User")
        
        # Login
        result = auth_manager.login("test@example.com", "TestPass123")
        
        assert result["success"] is True
        assert "token" in result
        assert "user" in result
        assert result["user"]["email"] == "test@example.com"
    
    def test_login_invalid_credentials(self, auth_manager):
        """Test login with invalid credentials."""
        auth_manager.register("test@example.com", "TestPass123", "Test User")
        
        result = auth_manager.login("test@example.com", "WrongPassword")
        
        assert result["success"] is False
        assert "error" in result
    
    def test_is_authenticated(self, auth_manager):
        """Test authentication check."""
        auth_manager.register("test@example.com", "TestPass123", "Test User")
        result = auth_manager.login("test@example.com", "TestPass123")
        token = result["token"]
        
        assert auth_manager.is_authenticated(token) is True
        assert auth_manager.is_authenticated("invalid_token") is False
    
    def test_get_current_user(self, auth_manager):
        """Test getting current user."""
        auth_manager.register("test@example.com", "TestPass123", "Test User")
        result = auth_manager.login("test@example.com", "TestPass123")
        token = result["token"]
        
        user = auth_manager.get_current_user(token)
        
        assert user is not None
        assert user["email"] == "test@example.com"
        assert user["full_name"] == "Test User"
    
    def test_logout(self, auth_manager):
        """Test logout functionality."""
        auth_manager.register("test@example.com", "TestPass123", "Test User")
        result = auth_manager.login("test@example.com", "TestPass123")
        token = result["token"]
        
        assert auth_manager.is_authenticated(token) is True
        
        logout_result = auth_manager.logout(token)
        
        assert logout_result["success"] is True
        assert auth_manager.is_authenticated(token) is False
    
    def test_require_auth(self, auth_manager):
        """Test require_auth raises error for invalid token."""
        with pytest.raises(ValueError, match="Authentication required"):
            auth_manager.require_auth("invalid_token")
    
    def test_require_role(self, auth_manager):
        auth_manager.register("user@example.com", "Pass1234", "User", role="user")
        user_token = auth_manager.login("user@example.com", "Pass1234")["token"]
        auth_manager.register("admin@example.com", "Pass1234", "Admin", role="admin")
        admin_token = auth_manager.login("admin@example.com", "Pass1234")["token"]
        admin = auth_manager.require_role(admin_token, "admin")
        assert admin["role"] == "admin"
        with pytest.raises(ValueError, match="Role 'admin' required"):
            auth_manager.require_role(user_token, "admin")
    
    def test_change_password(self, auth_manager):
        """Test password change."""
        auth_manager.register("test@example.com", "OldPass123", "Test User")
        result = auth_manager.login("test@example.com", "OldPass123")
        token = result["token"]
        
        # Change password
        result = auth_manager.change_password(token, "OldPass123", "NewPass456")
        
        assert result["success"] is True
        
        # Old password should not work
        login_result = auth_manager.login("test@example.com", "OldPass123")
        assert login_result["success"] is False
        
        # New password should work
        login_result = auth_manager.login("test@example.com", "NewPass456")
        assert login_result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
