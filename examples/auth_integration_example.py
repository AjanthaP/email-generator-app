"""
Example: Email Generator App with Authentication

This example shows how to integrate the authentication module
with the existing email generator Streamlit app.

To use:
1. Run: streamlit run examples/auth_integration_example.py
2. Register a new account or login
3. Generate emails with your authenticated profile
"""

import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.auth.streamlit_auth import StreamlitAuth
from src.workflow.langgraph_flow import execute_workflow

# Page config
st.set_page_config(
    page_title="Email Generator with Auth",
    page_icon="📧",
    layout="wide"
)

# Initialize authentication
auth_helper = StreamlitAuth()

# Check authentication
if not auth_helper.is_authenticated():
    st.title("📧 Email Generator App")
    st.markdown("### Please login or register to continue")
    
    # Show login/register page
    auth_helper.login_page()
    st.stop()

# User is authenticated - show main app
user = auth_helper.get_current_user()

# Sidebar with user info
st.sidebar.title("📧 Email Generator")
st.sidebar.markdown("---")

# User menu
auth_helper.user_menu()

# Profile section
with st.sidebar.expander("👤 My Profile"):
    st.write(f"**Name:** {user['full_name']}")
    st.write(f"**Email:** {user['email']}")
    st.write(f"**User ID:** {user['user_id']}")
    st.write(f"**Role:** {user['role']}")
    st.write(f"**Member since:** {user['created_at'][:10]}")

# Settings
with st.sidebar.expander("⚙️ Settings"):
    auth_helper.change_password_form()

# Main content
st.title(f"Welcome {user['full_name']}! 👋")
st.markdown("Generate professional emails powered by AI")

# Email composition tab
tab1, tab2 = st.tabs(["✍️ Compose", "📋 History"])

with tab1:
    st.subheader("Compose Email")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        recipient = st.text_input("Recipient", placeholder="e.g., John Smith")
        email_purpose = st.text_area(
            "Describe your email",
            placeholder="What do you want to communicate?",
            height=150
        )
    
    with col2:
        tone = st.selectbox(
            "Tone",
            ["formal", "casual", "friendly", "professional"]
        )
        length = st.slider("Preferred Length (words)", 50, 300, 150)
    
    use_stub = st.checkbox("Use stub mode (no AI)", value=False)
    
    if st.button("✨ Generate Email", type="primary"):
        if not email_purpose:
            st.error("Please describe your email")
        else:
            with st.spinner("Generating your email..."):
                try:
                    # Build prompt
                    prompt = email_purpose
                    if recipient:
                        prompt = f"Recipient: {recipient}\n\n{prompt}"
                    
                    # Generate email using authenticated user_id
                    state = execute_workflow(
                        user_input=prompt,
                        use_stub=use_stub,
                        user_id=user['user_id']  # Use authenticated user ID
                    )
                    
                    # Get draft
                    draft = (
                        state.get("final_draft") or 
                        state.get("personalized_draft") or 
                        state.get("styled_draft") or 
                        state.get("draft") or 
                        "No draft generated"
                    )
                    
                    # Display result
                    st.success("Email generated successfully!")
                    
                    st.markdown("### Your Email Draft")
                    st.markdown("---")
                    st.markdown(draft)
                    
                    # Metadata
                    with st.expander("📊 Generation Details"):
                        metadata = state.get("metadata", {})
                        st.json(metadata)
                    
                    # Copy button
                    st.button("📋 Copy to Clipboard")
                    
                except Exception as e:
                    st.error(f"Error generating email: {str(e)}")
                    st.info("Please check your configuration and try again")

with tab2:
    st.subheader("Email History")
    st.info("Email history feature coming soon!")
    st.markdown("Your previously generated emails will appear here.")

# Footer
st.markdown("---")
st.caption(f"Logged in as {user['email']} | Email Generator App v1.0")

# Admin section (if user is admin)
if user.get("role") == "admin":
    st.sidebar.markdown("---")
    with st.sidebar.expander("🔧 Admin Panel"):
        st.markdown("### Admin Controls")
        
        if st.button("View System Stats"):
            stats = auth_helper.auth.get_stats()
            st.json(stats)
        
        if st.button("Cleanup Sessions"):
            auth_helper.auth.cleanup_sessions()
            st.success("Sessions cleaned up!")
