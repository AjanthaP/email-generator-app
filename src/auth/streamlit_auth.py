"""
Streamlit Authentication Helper.

Provides Streamlit-specific authentication UI components and session integration.
"""

import streamlit as st
from typing import Optional, Dict, Callable
from .auth_manager import AuthManager


class StreamlitAuth:
    """
    Streamlit authentication helper.
    
    Provides ready-to-use authentication UI components for Streamlit apps.
    Integrates with Streamlit's session state for seamless user experience.
    
    Example:
        >>> auth_helper = StreamlitAuth()
        >>> # Show login page
        >>> user = auth_helper.login_page()
        >>> if user:
        ...     st.write(f"Welcome {user['full_name']}")
    """
    
    def __init__(self, auth_manager: Optional[AuthManager] = None):
        """
        Initialize Streamlit Auth Helper.
        
        Args:
            auth_manager: AuthManager instance (creates default if not provided)
        """
        self.auth = auth_manager or AuthManager()
        
        # Initialize session state
        if "auth_token" not in st.session_state:
            st.session_state.auth_token = None
        if "current_user" not in st.session_state:
            st.session_state.current_user = None
    
    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        if not st.session_state.auth_token:
            return False
        
        # Verify token is still valid
        user = self.auth.get_current_user(st.session_state.auth_token)
        if user:
            st.session_state.current_user = user
            return True
        else:
            # Token expired or invalid
            st.session_state.auth_token = None
            st.session_state.current_user = None
            return False
    
    def get_current_user(self) -> Optional[Dict]:
        """
        Get current authenticated user.
        
        Returns:
            User dict or None if not authenticated
        """
        if self.is_authenticated():
            return st.session_state.current_user
        return None
    
    def login_form(self) -> bool:
        """
        Display login form.
        
        Returns:
            True if login successful, False otherwise
        """
        with st.form("login_form"):
            st.subheader("🔐 Login")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            remember_me = st.checkbox("Remember me")
            
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if not email or not password:
                    st.error("Please enter email and password")
                    return False
                
                result = self.auth.login(email, password, remember_me)
                
                if result["success"]:
                    st.session_state.auth_token = result["token"]
                    st.session_state.current_user = result["user"]
                    st.success("Login successful!")
                    st.rerun()
                    return True
                else:
                    st.error(result.get("error", "Login failed"))
                    return False
        
        return False
    
    def register_form(self) -> bool:
        """
        Display registration form.
        
        Returns:
            True if registration successful, False otherwise
        """
        with st.form("register_form"):
            st.subheader("📝 Register")
            full_name = st.text_input("Full Name", key="reg_name")
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Password", type="password", key="reg_password")
            password_confirm = st.text_input("Confirm Password", type="password", key="reg_password_confirm")
            
            submitted = st.form_submit_button("Register")
            
            if submitted:
                if not all([full_name, email, password, password_confirm]):
                    st.error("Please fill in all fields")
                    return False
                
                if password != password_confirm:
                    st.error("Passwords do not match")
                    return False
                
                result = self.auth.register(email, password, full_name)
                
                if result["success"]:
                    st.success("Registration successful! Please login.")
                    return True
                else:
                    st.error(result.get("error", "Registration failed"))
                    return False
        
        return False
    
    def login_page(self) -> Optional[Dict]:
        """
        Display complete login/register page.
        
        Returns:
            User dict if authenticated, None otherwise
        """
        if self.is_authenticated():
            return st.session_state.current_user
        
        st.title("🔐 Authentication")
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            self.login_form()
        
        with tab2:
            self.register_form()
        
        return None
    
    def logout(self):
        """Logout current user."""
        if st.session_state.auth_token:
            self.auth.logout(st.session_state.auth_token)
        
        st.session_state.auth_token = None
        st.session_state.current_user = None
        st.rerun()
    
    def require_auth(self, login_page_callback: Optional[Callable] = None):
        """
        Require authentication - shows login page if not authenticated.
        
        Args:
            login_page_callback: Optional custom login page function
        """
        if not self.is_authenticated():
            if login_page_callback:
                login_page_callback()
            else:
                self.login_page()
            st.stop()
    
    def user_menu(self):
        """Display user menu in sidebar."""
        if not self.is_authenticated():
            return
        
        user = st.session_state.current_user
        
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"**👤 {user['full_name']}**")
            st.caption(f"{user['email']}")
            
            if st.button("🚪 Logout", key="logout_btn"):
                self.logout()
    
    def change_password_form(self) -> bool:
        """
        Display change password form.
        
        Returns:
            True if password changed successfully, False otherwise
        """
        if not self.is_authenticated():
            st.error("Please login first")
            return False
        
        with st.form("change_password_form"):
            st.subheader("🔑 Change Password")
            old_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            new_password_confirm = st.text_input("Confirm New Password", type="password")
            
            submitted = st.form_submit_button("Change Password")
            
            if submitted:
                if not all([old_password, new_password, new_password_confirm]):
                    st.error("Please fill in all fields")
                    return False
                
                if new_password != new_password_confirm:
                    st.error("New passwords do not match")
                    return False
                
                result = self.auth.change_password(
                    st.session_state.auth_token,
                    old_password,
                    new_password
                )
                
                if result["success"]:
                    st.success("Password changed successfully!")
                    return True
                else:
                    st.error(result.get("error", "Failed to change password"))
                    return False
        
        return False
