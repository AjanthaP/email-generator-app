import sys
import os
from pathlib import Path

import streamlit as st

# Add the project root to sys.path so absolute imports work
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.workflow.langgraph_flow import execute_workflow
from src.memory.memory_manager import MemoryManager


def main():
    st.set_page_config(page_title="✉️ AI Email Assistant", page_icon="✉️", layout="wide")

    # Custom CSS
    st.markdown(
        """
    <style>
        .stButton>button { width: 100%; }
        .draft-box { background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin: 10px 0; }
    </style>
    """,
        unsafe_allow_html=True,
    )

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
    use_stub = st.sidebar.checkbox(
        "Use stub (no Gemini)",
        value=False,
        help=(
            "When enabled, runs a local stub path and avoids calling the Gemini API. "
            "You can also set the DONOTUSEGEMINI env var or run with -donotusegemini."
        ),
    )

    # Initialize memory manager
    memory = MemoryManager()

    # Tabs: Compose / Templates / History
    tab1, tab2, tab3 = st.tabs(["✍️ Compose", "📝 Templates", "📚 History"]) 

    # --- Compose Tab ---
    with tab1:
        col1, col2 = st.columns([2, 1])

        with col1:
            user_prompt = st.text_area(
                "Describe your email:",
                placeholder=(
                    "Example: Write a follow-up email to John Smith from TechCorp thanking him for yesterday's meeting "
                    "and proposing next steps for our collaboration..."
                ),
                height=220,
                key="compose_prompt",
            )

            recipient = st.text_input("Recipient Name (optional):", placeholder="John Smith", key="compose_recipient")
            recipient_email = st.text_input("Recipient Email (optional):", placeholder="name@company.com", key="compose_recipient_email")

            generate_btn = st.button("✨ Generate Email", key="generate_main")

        with col2:
            st.info(
                "💡 Tips for best results:\n\n- Be specific about the email purpose\n- Mention key points to include\n- Specify the recipient's role or company\n- Include any relevant context\n- Try different tones to see variations"
            )

        # Generate handling
        if generate_btn:
            if not user_prompt:
                st.error("⚠️ Please describe your email request")
            else:
                with st.spinner("🤖 Crafting your email..."):
                    # Prepare prompt
                    full_prompt = user_prompt
                    if recipient:
                        full_prompt = f"Recipient: {recipient}\n\n{user_prompt}"
                    if recipient_email:
                        full_prompt = f"Recipient: {recipient}\nRecipient Email: {recipient_email}\nLength preference: {length_pref}\n\n{full_prompt}"

                    try:
                        state = execute_workflow(full_prompt, use_stub=use_stub)

                        # Prefer final_draft if present, else draft
                        draft = (
                            state.get("final_draft")
                            or state.get("personalized_draft")
                            or state.get("styled_draft")
                            or state.get("draft")
                        )

                        st.session_state["last_draft"] = draft
                        # Include metadata from the workflow (source/model) for UI indicator
                        workflow_meta = state.get("metadata", {})
                        st.session_state["last_metadata"] = {
                            "intent": state.get("intent", ""),
                            "recipient": state.get("recipient", recipient),
                            "recipient_email": recipient_email,
                            "tone": state.get("tone", tone),
                            "source": workflow_meta.get("source", "llm"),
                            "model": workflow_meta.get("model") or workflow_meta.get("fallback_from_model"),
                        }

                        # Store review notes if present
                        st.session_state["last_review_notes"] = state.get("review_notes", {})

                        if save_to_history:
                            memory.save_draft(user_id, {"draft": draft, "metadata": st.session_state["last_metadata"]})

                    except Exception as e:
                        st.error(f"Error generating email: {str(e)}")
                        st.info("Please check your API key, quota, and try again")

        # Display result area
        if "last_draft" in st.session_state:
            st.markdown("---")
            st.header("📧 Your Email Draft")

            # Visual indicator
            last_meta = st.session_state.get("last_metadata", {})
            source = last_meta.get("source", "llm")
            model = last_meta.get("model")
            if source == "stub":
                st.warning(
                    "Offline stub used for generation. (This can happen when you checked 'Use stub' or the LLM quota was exceeded.)"
                )
            else:
                if model:
                    st.success(f"Generated by LLM: {model}")
                else:
                    st.success("Generated by LLM")

            # Show review notes / fallback reason if present
            review_notes = st.session_state.get("last_review_notes", {})
            if review_notes:
                with st.expander("🔍 Review Notes / Fallback Reason"):
                    for k, v in review_notes.items():
                        st.write(f"**{k}**: {v}")

            metadata = st.session_state.get("last_metadata", {})

            if show_metadata:
                mcol1, mcol2, mcol3 = st.columns(3)
                with mcol1:
                    st.metric("📋 Intent", (metadata.get("intent") or "N/A").replace("_", " ").title())
                with mcol2:
                    st.metric("🎭 Tone", (metadata.get("tone") or "N/A").title())
                with mcol3:
                    st.metric("👤 Recipient", metadata.get("recipient", "N/A"))

            # Editable draft box
            with st.container():
                st.markdown("<div class='draft-box'>", unsafe_allow_html=True)
                edited_draft = st.text_area("Edit your email:", value=st.session_state["last_draft"], height=300, key="email_editor")
                st.markdown("</div>", unsafe_allow_html=True)

            # Character/word count
            word_count = len(edited_draft.split())
            char_count = len(edited_draft)
            st.caption(f"📊 {word_count} words • {char_count} characters")

            # Action buttons
            col_txt, col_md, col_copy, col_regen = st.columns(4)
            with col_txt:
                st.download_button("📥 Download TXT", edited_draft, file_name="email_draft.txt", mime="text/plain")
            with col_md:
                st.download_button("📄 Download MD", edited_draft, file_name="email_draft.md", mime="text/markdown")
            with col_copy:
                if st.button("📋 Copy to Clipboard"):
                    st.code(edited_draft)
                    st.success("Draft displayed above - select and copy!")
            with col_regen:
                if st.button("🔄 Generate New"):
                    # Learn from edits
                    if edited_draft != st.session_state.get("last_draft"):
                        memory.learn_from_edits(user_id, st.session_state.get("last_draft"), edited_draft)

                    # Clear last draft and keep prompt for editing
                    del st.session_state["last_draft"]
                    st.experimental_rerun()

    # --- Templates Tab ---
    with tab2:
        st.header("📝 Email Templates")
        st.markdown("Quick start with pre-built templates")

        templates = {
            "Cold Outreach": {
                "prompt": "Write a cold outreach email to a potential client introducing our AI consulting services",
                "tone": "formal",
                "description": "Professional introduction to prospects",
            },
            "Meeting Follow-up": {
                "prompt": "Write a follow-up email after our product demo meeting, thanking them and proposing next steps",
                "tone": "formal",
                "description": "Post-meeting thank you and next steps",
            },
            "Thank You Note": {
                "prompt": "Write a thank you email for their time and valuable feedback on our product",
                "tone": "empathetic",
                "description": "Genuine gratitude expression",
            },
            "Project Update": {
                "prompt": "Write a status update email about the Q4 project progress to stakeholders",
                "tone": "formal",
                "description": "Professional status update",
            },
            "Networking": {
                "prompt": "Write a LinkedIn connection follow-up email to continue the conversation we started at the conference",
                "tone": "casual",
                "description": "Friendly professional networking",
            },
            "Apology": {
                "prompt": "Write an apology email for missing the scheduled meeting due to an emergency",
                "tone": "empathetic",
                "description": "Sincere apology and rescheduling",
            },
        }

        tcol1, tcol2 = st.columns(2)
        for idx, (name, data) in enumerate(templates.items()):
            col = tcol1 if idx % 2 == 0 else tcol2
            with col:
                st.subheader(name)
                st.write(data["description"])
                if st.button(f"Use: {name}", key=f"tpl_{idx}"):
                    # Populate compose prompt and set tone
                    st.session_state["compose_prompt"] = data["prompt"]
                    # Change tone selection in sidebar (no direct API to set selectbox, store desired)
                    # We'll store desired template tone in session for the user to apply
                    st.session_state["template_tone"] = data["tone"]
                    st.experimental_rerun()

    # If a template tone was chosen, show a small banner suggesting the tone
    if st.session_state.get("template_tone"):
        st.sidebar.info(f"Template suggested tone: {st.session_state.get('template_tone')}")

    # --- History Tab ---
    with tab3:
        st.header("📚 Draft History")
        history = memory.get_draft_history(user_id, limit=20)
        if not history:
            st.info("No draft history yet. Start composing emails to see them here!")
        else:
            st.markdown(f"Showing last {len(history)} drafts")
            for idx, draft_entry in enumerate(history):
                title = f"📧 {draft_entry.get('metadata', {}).get('intent', 'Email').title()} • {draft_entry.get('timestamp', '')[:10]}"
                with st.expander(title):
                    st.write(draft_entry.get("draft", ""))
                    met = draft_entry.get("metadata", {})
                    st.write(met)
                    if st.button(f"Reuse draft #{idx+1}", key=f"reuse_{idx}"):
                        st.session_state["compose_prompt"] = draft_entry.get("draft", "")
                        st.experimental_rerun()


if __name__ == "__main__":
    main()
