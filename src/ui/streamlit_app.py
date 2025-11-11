import sys
import os
from typing import Optional

# Ensure src package is importable when running from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st

from src.workflow.langgraph_flow import execute_workflow, default_graph_order
from src.memory.memory_manager import MemoryManager


def main():
    st.set_page_config(page_title="AI Email Assistant", page_icon="✉️", layout="wide")

    st.title("✉️ AI Email Assistant")
    st.markdown("Generate professional, personalized emails in seconds")

    # Sidebar
    st.sidebar.header("⚙️ Configuration")

    user_id = st.sidebar.text_input("User ID", value="default", help="Your unique identifier")

    tone = st.sidebar.selectbox(
        "Email Tone",
        ["formal", "casual", "assertive", "empathetic"],
        help="Choose the tone for your email",
    )

    length_pref = st.sidebar.slider("Preferred Length (words)", 50, 500, 150, 50)

    show_metadata = st.sidebar.checkbox("Show metadata", value=True)
    save_to_history = st.sidebar.checkbox("Save to history", value=True)

    # Initialize memory manager
    memory = MemoryManager()

    # Layout
    col1, col2 = st.columns([1, 1])

    with col1:
        user_prompt = st.text_area(
            "Describe your email:",
            placeholder=(
                "Example: Write a follow-up email to John Smith from TechCorp thanking him for yesterday's meeting "
                "and proposing next steps for our collaboration..."
            ),
            height=200,
        )

        recipient = st.text_input("Recipient Name (optional):", placeholder="John Smith")
        recipient_email = st.text_input("Recipient Email (optional):", placeholder="name@company.com")

        generate_btn = st.button("✨ Generate Email")

    with col2:
        st.info(
            "💡 Tips for best results:\n\n- Be specific about the email purpose\n- Mention key points to include\n- Specify the recipient's role or company\n- Include any relevant context"
        )

    if generate_btn:
        if not user_prompt:
            st.error("Please describe your email request")
        else:
            with st.spinner("🤖 Crafting your email..."):
                # Add recipient to prompt if provided
                full_prompt = user_prompt
                if recipient:
                    full_prompt = f"Recipient: {recipient}\n\n{user_prompt}"
                if recipient_email:
                    # Add recipient email as additional context for parsing/personalization
                    full_prompt = f"Recipient Email: {recipient_email}\n\n{full_prompt}"

                try:
                    state = execute_workflow(full_prompt)

                    # Prefer final_draft if present, else draft
                    draft = state.get("final_draft") or state.get("personalized_draft") or state.get("styled_draft") or state.get("draft")

                    st.session_state["last_draft"] = draft
                    st.session_state["last_metadata"] = {
                        "intent": state.get("intent", ""),
                        "recipient": state.get("recipient", recipient),
                        "recipient_email": recipient_email,
                        "tone": state.get("tone", tone),
                    }

                    if save_to_history:
                        memory.save_draft(user_id, {"draft": draft, "metadata": st.session_state["last_metadata"]})

                except Exception as e:
                    st.error(f"Error generating email: {str(e)}")
                    st.info("Please check your API key, quota, and try again")

    # Display result
    if "last_draft" in st.session_state:
        st.header("📧 Your Email Draft")

        metadata = st.session_state.get("last_metadata", {})

        mcol1, mcol2, mcol3 = st.columns(3)
        with mcol1:
            st.metric("Intent", (metadata.get("intent") or "N/A").replace("_", " ").title())
        with mcol2:
            st.metric("Tone", (metadata.get("tone") or "N/A").title())
        with mcol3:
            st.metric("Recipient", metadata.get("recipient", "N/A"))

        edited_draft = st.text_area("Edit your email:", value=st.session_state["last_draft"], height=300, key="email_editor")

        bcol1, bcol2, bcol3 = st.columns(3)
        with bcol1:
            st.download_button("📥 Download as TXT", edited_draft, file_name="email_draft.txt", mime="text/plain")

        with bcol2:
            if st.button("📋 Copy to Clipboard"):
                st.code(edited_draft)
                st.success("Draft displayed above - select and copy!")

        with bcol3:
            if st.button("🔄 Generate New"):
                del st.session_state["last_draft"]
                st.experimental_rerun()

    # Templates tab / history can be added in future iterations


if __name__ == "__main__":
    main()
