"""
User Manager - Handles user registration, authentication, and profile management.
"""

import json
import os
import hashlib
import secrets
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path


class UserManager:
    """
    Manages user accounts, credentials, and profiles.
    
    Features:
    - User registration with email/password
    - Secure password hashing (SHA-256 with salt)
    - User profile management
    - Role-based access control (user, admin)
    - Account status management (active, suspended, deleted)
    
    Example:
        >>> user_mgr = UserManager()
        >>> user_mgr.register_user("user@example.com", "SecurePass123", "John Doe")
        >>> if user_mgr.verify_credentials("user@example.com", "SecurePass123"):
        ...     user = user_mgr.get_user("user@example.com")
    """
    
    def __init__(self, users_file: str = "data/users/users.json"):
        """
        Initialize User Manager.
        
        Args:
            users_file: Path to JSON file storing user data
        """
        self.users_file = users_file
        self.users: Dict[str, Dict] = {}
        self._ensure_data_dir()
        self._load_users()
    
    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist."""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
    
    def _load_users(self):
        """Load users from JSON file."""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.users = {}
    
    def _save_users(self):
        """Save users to JSON file."""
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def _hash_password(self, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Hash password with salt using SHA-256.
        
        Args:
            password: Plain text password
            salt: Optional salt (generated if not provided)
            
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_hex(32)
        
        pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return pwd_hash, salt
    
    def register_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str = "user",
        metadata: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Register a new user.
        
        Args:
            email: User's email address (unique identifier)
            password: Plain text password (will be hashed)
            full_name: User's full name
            role: User role (user, admin)
            metadata: Additional user metadata
            
        Returns:
            Dict with registration result (success/error message)
            
        Raises:
            ValueError: If email is already registered
        """
        # Normalize email
        email = email.lower().strip()
        
        # Check if user already exists
        if email in self.users:
            raise ValueError(f"User with email {email} already exists")
        
        # Validate password strength
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Hash password
        pwd_hash, salt = self._hash_password(password)
        
        # Generate user ID
        user_id = secrets.token_urlsafe(16)
        
        # Create user record
        self.users[email] = {
            "user_id": user_id,
            "email": email,
            "password_hash": pwd_hash,
            "salt": salt,
            "full_name": full_name,
            "role": role,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "last_login": None,
            "metadata": metadata or {}
        }
        
        self._save_users()
        
        return {
            "success": True,
            "user_id": user_id,
            "message": f"User {email} registered successfully"
        }
    
    def verify_credentials(self, email: str, password: str) -> bool:
        """
        Verify user credentials.
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            True if credentials are valid, False otherwise
        """
        email = email.lower().strip()
        
        if email not in self.users:
            return False
        
        user = self.users[email]
        
        # Check if account is active
        if user.get("status") != "active":
            return False
        
        # Verify password
        pwd_hash, _ = self._hash_password(password, user["salt"])
        
        if pwd_hash == user["password_hash"]:
            # Update last login
            user["last_login"] = datetime.utcnow().isoformat()
            self._save_users()
            return True
        
        return False
    
    def get_user(self, email: str) -> Optional[Dict]:
        """
        Get user information by email.
        
        Args:
            email: User's email address
            
        Returns:
            User dict (without sensitive fields) or None if not found
        """
        email = email.lower().strip()
        
        if email not in self.users:
            return None
        
        user = self.users[email].copy()
        
        # Remove sensitive fields
        user.pop("password_hash", None)
        user.pop("salt", None)
        
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """
        Get user information by user_id.
        
        Args:
            user_id: User's unique ID
            
        Returns:
            User dict (without sensitive fields) or None if not found
        """
        for email, user in self.users.items():
            if user.get("user_id") == user_id:
                user_copy = user.copy()
                user_copy.pop("password_hash", None)
                user_copy.pop("salt", None)
                return user_copy
        return None
    
    def update_user(self, email: str, updates: Dict) -> bool:
        """
        Update user information.
        
        Args:
            email: User's email address
            updates: Dict of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        email = email.lower().strip()
        
        if email not in self.users:
            return False
        
        # Prevent updating sensitive fields directly
        protected_fields = ["password_hash", "salt", "user_id", "created_at"]
        for field in protected_fields:
            updates.pop(field, None)
        
        # Update user
        self.users[email].update(updates)
        self._save_users()
        
        return True
    
    def change_password(self, email: str, old_password: str, new_password: str) -> bool:
        """
        Change user password.
        
        Args:
            email: User's email address
            old_password: Current password
            new_password: New password
            
        Returns:
            True if successful, False otherwise
        """
        # Verify old password
        if not self.verify_credentials(email, old_password):
            return False
        
        # Validate new password
        if len(new_password) < 8:
            raise ValueError("New password must be at least 8 characters long")
        
        email = email.lower().strip()
        
        # Hash new password
        pwd_hash, salt = self._hash_password(new_password)
        
        # Update password
        self.users[email]["password_hash"] = pwd_hash
        self.users[email]["salt"] = salt
        self._save_users()
        
        return True
    
    def delete_user(self, email: str) -> bool:
        """
        Delete user account (soft delete - marks as deleted).
        
        Args:
            email: User's email address
            
        Returns:
            True if successful, False otherwise
        """
        email = email.lower().strip()
        
        if email not in self.users:
            return False
        
        # Soft delete - mark as deleted instead of removing
        self.users[email]["status"] = "deleted"
        self.users[email]["deleted_at"] = datetime.utcnow().isoformat()
        self._save_users()
        
        return True
    
    def list_users(self, role: Optional[str] = None, status: str = "active") -> List[Dict]:
        """
        List all users with optional filtering.
        
        Args:
            role: Filter by role (user, admin) or None for all
            status: Filter by status (active, suspended, deleted)
            
        Returns:
            List of user dicts (without sensitive fields)
        """
        users = []
        
        for email, user in self.users.items():
            # Filter by status
            if user.get("status") != status:
                continue
            
            # Filter by role
            if role and user.get("role") != role:
                continue
            
            # Create safe copy
            user_copy = user.copy()
            user_copy.pop("password_hash", None)
            user_copy.pop("salt", None)
            users.append(user_copy)
        
        return users
    
    def user_exists(self, email: str) -> bool:
        """
        Check if user exists.
        
        Args:
            email: User's email address
            
        Returns:
            True if user exists, False otherwise
        """
        return email.lower().strip() in self.users
