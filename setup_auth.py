"""
Authentication Module Setup Script

Run this script to initialize the authentication system and create initial users.

Usage:
    python setup_auth.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.auth import AuthManager


def main():
    """Initialize authentication system."""
    print("=" * 60)
    print("Email Generator App - Authentication Setup")
    print("=" * 60)
    print()
    
    # Initialize auth manager
    print("Initializing authentication system...")
    auth = AuthManager()
    print("✓ Authentication system initialized")
    print()
    
    # Check if admin exists
    admin_exists = auth.user_manager.user_exists("admin@example.com")
    
    if not admin_exists:
        print("Creating default admin account...")
        try:
            auth.register(
                email="admin@example.com",
                password="Admin123!",
                full_name="Admin User",
                role="admin"
            )
            print("✓ Admin account created")
            print("  Email: admin@example.com")
            print("  Password: Admin123!")
            print("  ⚠️  CHANGE THIS PASSWORD AFTER FIRST LOGIN!")
            print()
        except Exception as e:
            print(f"✗ Error creating admin account: {e}")
            print()
    else:
        print("ℹ Admin account already exists")
        print()
    
    # Check if test user exists
    user_exists = auth.user_manager.user_exists("user@example.com")
    
    if not user_exists:
        print("Creating test user account...")
        try:
            auth.register(
                email="user@example.com",
                password="User123!",
                full_name="Test User",
                role="user"
            )
            print("✓ Test user account created")
            print("  Email: user@example.com")
            print("  Password: User123!")
            print()
        except Exception as e:
            print(f"✗ Error creating test user: {e}")
            print()
    else:
        print("ℹ Test user already exists")
        print()
    
    # Display stats
    stats = auth.get_stats()
    print("System Status:")
    print(f"  Total users: {stats['total_active_users']}")
    print(f"  Active sessions: {stats['active_sessions']}")
    print()
    
    # Display file locations
    print("Data Storage:")
    print(f"  Users: {auth.user_manager.users_file}")
    print(f"  Sessions: {auth.session_manager.sessions_file}")
    print()
    
    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Run the example app:")
    print("   streamlit run examples/auth_integration_example.py")
    print()
    print("2. Or integrate with your main app:")
    print("   See AUTHENTICATION_MODULE_SUMMARY.md for details")
    print()
    print("3. Change default passwords after first login!")
    print()


if __name__ == "__main__":
    main()
