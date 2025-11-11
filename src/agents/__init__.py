"""
Email Assistant Agents Package

This package contains all agent implementations for the AI-powered email assistant.
Each agent has a specific role in the email generation workflow.

Available Agents:
- InputParserAgent: Extracts structured data from user input
- IntentDetectorAgent: Classifies email intent
- DraftWriterAgent: Generates email body based on intent
- ToneStylistAgent: Adjusts email tone while preserving content
- PersonalizationAgent: Injects user-specific data
- ReviewAgent: Validates and improves drafts
- RouterAgent: Handles workflow routing and fallbacks
"""

from src.agents.input_parser import InputParserAgent, ParsedInput
from src.agents.intent_detector import IntentDetectorAgent, EmailIntent

__all__ = [
    "InputParserAgent",
    "IntentDetectorAgent",
    "EmailIntent",
    "ParsedInput",
]
