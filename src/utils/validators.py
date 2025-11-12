"""
Input validation utilities for email assistant.
Provides functions to validate user input and generated emails.
"""

from typing import Dict, List, Optional
import re


class InputValidator:
    """Validates user input for email composition"""
    
    MIN_INPUT_LENGTH = 10
    MAX_INPUT_LENGTH = 5000
    
    @staticmethod
    def validate_user_input(user_input: str) -> tuple[bool, Optional[str]]:
        """
        Validate user input for email request.
        
        Args:
            user_input: User's email composition request
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not user_input:
            return False, "Input cannot be empty"
        
        if len(user_input) < InputValidator.MIN_INPUT_LENGTH:
            return False, f"Input must be at least {InputValidator.MIN_INPUT_LENGTH} characters"
        
        if len(user_input) > InputValidator.MAX_INPUT_LENGTH:
            return False, f"Input cannot exceed {InputValidator.MAX_INPUT_LENGTH} characters"
        
        return True, None
    
    @staticmethod
    def validate_email(email: str) -> tuple[bool, Optional[str]]:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return True, None  # Email is optional
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email address format"
        
        return True, None
    
    @staticmethod
    def validate_tone(tone: str) -> tuple[bool, Optional[str]]:
        """
        Validate tone preference.
        
        Args:
            tone: Tone preference
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        valid_tones = ["formal", "casual", "assertive", "empathetic"]
        
        if tone.lower() not in valid_tones:
            return False, f"Tone must be one of: {', '.join(valid_tones)}"
        
        return True, None


class DraftValidator:
    """Validates generated email drafts"""
    
    MIN_DRAFT_LENGTH = 30  # words
    MAX_DRAFT_LENGTH = 1000  # words
    
    @staticmethod
    def has_greeting(draft: str) -> bool:
        """Check if draft has a greeting"""
        greetings = ["dear", "hi", "hello", "hey"]
        return any(g in draft.lower()[:100] for g in greetings)
    
    @staticmethod
    def has_closing(draft: str) -> bool:
        """Check if draft has a closing"""
        closings = ["regards", "sincerely", "best", "thanks", "cheers", "respectfully"]
        return any(c in draft.lower()[-150:] for c in closings)
    
    @staticmethod
    def check_word_count(draft: str) -> tuple[int, bool]:
        """
        Check word count of draft.
        
        Returns:
            Tuple of (word_count, is_valid)
        """
        word_count = len(draft.split())
        is_valid = DraftValidator.MIN_DRAFT_LENGTH <= word_count <= DraftValidator.MAX_DRAFT_LENGTH
        return word_count, is_valid
    
    @staticmethod
    def check_punctuation(draft: str) -> Dict[str, int]:
        """
        Check punctuation usage in draft.
        
        Returns:
            Dictionary with counts of various punctuation marks
        """
        return {
            "exclamation_marks": draft.count("!"),
            "question_marks": draft.count("?"),
            "periods": draft.count("."),
            "commas": draft.count(","),
        }
    
    @staticmethod
    def validate_draft(draft: str) -> tuple[bool, List[str]]:
        """
        Comprehensive draft validation.
        
        Args:
            draft: Email draft to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check greeting
        if not DraftValidator.has_greeting(draft):
            issues.append("Missing greeting (Dear, Hi, Hello, Hey)")
        
        # Check closing
        if not DraftValidator.has_closing(draft):
            issues.append("Missing closing (Regards, Sincerely, Best, etc.)")
        
        # Check word count
        word_count, valid_length = DraftValidator.check_word_count(draft)
        if not valid_length:
            if word_count < DraftValidator.MIN_DRAFT_LENGTH:
                issues.append(f"Email too short ({word_count} words, minimum {DraftValidator.MIN_DRAFT_LENGTH})")
            else:
                issues.append(f"Email too long ({word_count} words, maximum {DraftValidator.MAX_DRAFT_LENGTH})")
        
        # Check punctuation
        punctuation = DraftValidator.check_punctuation(draft)
        if punctuation["exclamation_marks"] > 3:
            issues.append("Too many exclamation marks (max 3 recommended)")
        
        is_valid = len(issues) == 0
        return is_valid, issues


class IntentValidator:
    """Validates email intent classification"""
    
    VALID_INTENTS = [
        "outreach",
        "follow_up",
        "apology",
        "information_request",
        "thank_you",
        "meeting_request",
        "status_update",
        "introduction",
        "networking",
        "complaint"
    ]
    
    @staticmethod
    def validate_intent(intent: str) -> tuple[bool, Optional[str]]:
        """
        Validate email intent.
        
        Args:
            intent: Email intent classification
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if intent.lower() not in IntentValidator.VALID_INTENTS:
            return False, f"Invalid intent. Must be one of: {', '.join(IntentValidator.VALID_INTENTS)}"
        
        return True, None
