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
- RefinementAgent: Final polish - removes duplicates, fixes grammar, eliminates repetition
- RouterAgent: Handles workflow routing and fallbacks
"""

from src.agents.input_parser import InputParserAgent, ParsedInput
from src.agents.intent_detector import IntentDetectorAgent, EmailIntent
from src.agents.draft_writer import DraftWriterAgent
from src.agents.tone_stylist import ToneStylistAgent
from src.agents.personalization import PersonalizationAgent
from src.agents.review_agent import ReviewAgent
from src.agents.refinement import RefinementAgent
from src.agents.router import RouterAgent

__all__ = [
    "InputParserAgent",
    "IntentDetectorAgent",
    "DraftWriterAgent",
    "ToneStylistAgent",
    "PersonalizationAgent",
    "ReviewAgent",
    "RefinementAgent",
    "RouterAgent",
    "EmailIntent",
    "ParsedInput",
]
