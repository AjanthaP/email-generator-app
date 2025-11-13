"""
Personalization Agent - Adds user-specific personalization to emails.

This agent enhances the email with user-specific information like signatures,
company details, personal preferences, and personalization markers. It makes
emails feel more authentic and tailored to the user.
"""

from typing import Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import json
import os
from src.utils.llm_wrapper import LLMWrapper, make_wrapper


class PersonalizationAgent:
    """
    Adds personalization from user profile to emails.
    
    This agent incorporates user-specific information into the email:
    - User's signature
    - Professional title and company
    - Writing style preferences
    - Personal notes and customizations
    
    The agent maintains a user profile system that tracks preferences
    and learned personalization patterns from user edits.
    
    Example:
        >>> llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        >>> personalizer = PersonalizationAgent(llm)
        >>> personal_draft = personalizer.personalize(draft, user_id="user123")
    """
    
    def __init__(self, llm: ChatGoogleGenerativeAI, 
                 profile_path: str = "src/memory/user_profiles.json",
                 llm_wrapper: Optional[LLMWrapper] = None):
        """
        Initialize Personalization Agent.
        
        Args:
            llm: ChatGoogleGenerativeAI instance for processing
            profile_path: Path to user profiles JSON file
        """
        self.llm = llm
        self.llm_wrapper = llm_wrapper or make_wrapper(llm)
        self.profile_path = profile_path
        self.profiles = self._load_profiles()
        
        self.prompt = ChatPromptTemplate.from_template("""
        You are personalizing an email draft with user-specific information.
        
        Original Draft:
        {draft}
        
        User Profile:
        - Name: {user_name}
        - Title: {user_title}
        - Company: {user_company}
        - Signature: {signature}
        - Writing Style Notes: {style_notes}
        
        CRITICAL INSTRUCTIONS for personalization:
        1. Add the signature at the end
        2. ONLY use profile fields that have actual values (not empty strings)
        3. If Name is provided and not empty, use it in the signature and body where appropriate
        4. If Title is provided and not empty, use it where relevant (e.g., "I am [Title]")
        5. If Company is provided and not empty, use it where relevant (e.g., "at [Company]")
        6. NEVER generate placeholder text like "[Your Name]", "[Your Title]", "[Your Company]", or similar brackets
        7. If a field is empty, simply omit that information - do not create placeholders
        8. Match the user's preferred writing style
        9. Keep the core message intact
        
        Return ONLY the personalized email with NO placeholder brackets.
        """)
    
    def _load_profiles(self) -> Dict:
        """
        Load user profiles from JSON file.
        
        Returns:
            Dict: User profiles indexed by user_id
        """
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {"default": self._get_default_profile()}
        return {"default": self._get_default_profile()}
    
    def _get_default_profile(self) -> Dict:
        """
        Get default profile template.
        
        Returns:
            Dict: Default user profile structure
        """
        return {
            "user_name": "User",
            "user_title": "",
            "user_company": "",
            "signature": "\n\nBest regards",
            "style_notes": "professional and clear",
            "preferences": {
                "use_emojis": False,
                "include_phone": False,
                "preferred_length": 150
            }
        }
    
    def get_profile(self, user_id: str = "default") -> Dict:
        """
        Get user profile by ID. Prefer MemoryManager/DB when available,
        otherwise fall back to local JSON profiles.
        """
        # Try database-backed profile first
        try:
            from src.memory.memory_manager import MemoryManager  # local import to avoid cycles
            mm = MemoryManager()
            db_profile = mm.load_profile(user_id)
            if isinstance(db_profile, dict) and db_profile:
                # Normalize to the structure expected by the prompt
                prefs = db_profile.get("preferences", {}) if isinstance(db_profile.get("preferences"), dict) else {}
                return {
                    "user_name": db_profile.get("user_name") or db_profile.get("name") or "User",
                    "user_title": db_profile.get("user_title") or db_profile.get("role") or "",
                    "user_company": db_profile.get("user_company") or db_profile.get("company") or "",
                    "signature": db_profile.get("signature") or prefs.get("signature") or "\n\nBest regards",
                    "style_notes": db_profile.get("style_notes") or prefs.get("style_notes") or "professional and clear",
                    "preferences": prefs,
                }
        except Exception:
            # Silently fall back to file-based profile
            pass

        # Fallback to local JSON profiles
        return self.profiles.get(user_id, self._get_default_profile())
    
    def save_profile(self, user_id: str, profile_data: Dict):
        """
        Save user profile to file.
        
        Args:
            user_id: User identifier
            profile_data: Profile data to save
        """
        self.profiles[user_id] = profile_data
        
        os.makedirs(os.path.dirname(self.profile_path), exist_ok=True)
        with open(self.profile_path, 'w') as f:
            json.dump(self.profiles, f, indent=2)
    
    def personalize(self, draft: str, user_id: str = "default") -> str:
        """
        Add personalization to draft.
        
        Args:
            draft: Email draft to personalize
            user_id: User ID for profile lookup
            
        Returns:
            str: Personalized email draft
        """
        try:
            profile = self.get_profile(user_id)
            # Ensure the signature includes the user's name if available
            user_name = (profile.get("user_name") or "").strip()
            signature = profile.get("signature", "\n\nBest regards")
            try:
                sig_base = signature.strip()
                # Prepend spacing if missing
                if not sig_base.startswith("\n"):
                    sig_base = "\n\n" + sig_base
                # If name isn't already present, append it on a new line
                if user_name and user_name.lower() not in sig_base.lower():
                    if not sig_base.endswith(",") and not sig_base.endswith(",\n"):
                        sig_base = sig_base + ","
                    sig_final = f"{sig_base}\n{user_name}"
                else:
                    sig_final = sig_base
            except Exception:
                sig_final = profile.get("signature", "\n\nBest regards")

            chain = self.prompt | self.llm
            response = self.llm_wrapper.invoke_chain(chain, {
                "draft": draft,
                "user_name": profile.get("user_name", ""),
                "user_title": profile.get("user_title", ""),
                "user_company": profile.get("user_company", ""),
                "signature": sig_final,
                "style_notes": profile.get("style_notes", "professional")
            })
            
            return response.content.strip()
            
        except Exception as e:
            print(f"Error personalizing draft: {e}")
            # Add basic signature if personalization fails
            profile = self.get_profile(user_id)
            signature = profile.get("signature", "\n\nBest regards")
            return f"{draft}{signature}"
    
    def __call__(self, state: Dict) -> Dict:
        """
        LangGraph node function - processes state and returns updates.
        
        Args:
            state: Current workflow state with styled_draft and optional user_id
            
        Returns:
            Dict: Updated state with personalized draft
        """
        # Use styled_draft if available, otherwise use draft
        draft_to_personalize = state.get("styled_draft", state.get("draft", ""))
        
        personalized = self.personalize(
            draft_to_personalize,
            state.get("user_id", "default")
        )
        return {"personalized_draft": personalized}
