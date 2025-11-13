"""SQLAlchemy models for PostgreSQL database.

This module defines the database schema for user profiles and draft history.
Designed to work alongside ChromaDB when added later for semantic search.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class UserProfile(Base):
    """User profile table for storing authentication and preferences.
    
    This stores core user data from OAuth and manual updates.
    ChromaDB (when added) will handle semantic search over user's draft history.
    """
    __tablename__ = "user_profiles"

    # Primary identification
    id = Column(String(255), primary_key=True, index=True)  # user_id from OAuth or generated
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    
    # Profile details
    company = Column(String(255), nullable=True)
    role = Column(String(255), nullable=True)
    
    # OAuth information
    oauth_provider = Column(String(50), nullable=True)  # 'google', 'github', 'microsoft'
    oauth_user_id = Column(String(255), nullable=True)  # Provider's user ID
    
    # User preferences (stored as JSON for flexibility)
    preferences = Column(JSON, nullable=True, default=dict)
    # Example structure:
    # {
    #   "tone_preference": "professional",
    #   "preferred_length": 150,
    #   "default_context": "...",
    #   "learned_preferences": {...}
    # }
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    drafts = relationship("Draft", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserProfile(id={self.id}, email={self.email}, name={self.name})>"


class Draft(Base):
    """Draft history table for storing email generations.
    
    Stores all email drafts with metadata for history tracking.
    When ChromaDB is added, embeddings will reference these draft IDs.
    """
    __tablename__ = "drafts"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to user
    user_id = Column(String(255), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Draft content
    content = Column(Text, nullable=False)  # The actual email text
    original_input = Column(Text, nullable=True)  # User's original request
    
    # Metadata (stored as JSON for flexibility)
    metadata = Column(JSON, nullable=True, default=dict)
    # Example structure:
    # {
    #   "tone": "professional",
    #   "length": "medium",
    #   "recipient": "...",
    #   "context": "...",
    #   "word_count": 150,
    #   "intent": "request",
    #   "formality_score": 0.8,
    #   "was_edited": false,
    #   "edit_distance": 0
    # }
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationship
    user = relationship("UserProfile", back_populates="drafts")
    
    def __repr__(self):
        return f"<Draft(id={self.id}, user_id={self.user_id}, created_at={self.created_at})>"


class OAuthSession(Base):
    """OAuth session table for tracking active authentication flows.
    
    Stores OAuth state parameters temporarily during the auth flow.
    This replaces the in-memory dictionary for stateless operation.
    """
    __tablename__ = "oauth_sessions"

    # OAuth state parameter (used as primary key)
    state = Column(String(255), primary_key=True, index=True)
    
    # Session data
    provider = Column(String(50), nullable=False)  # 'google', 'github', 'microsoft'
    redirect_uri = Column(String(512), nullable=False)
    code_verifier = Column(String(255), nullable=True)  # For PKCE flow
    
    # Session metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)  # Auto-cleanup after 10 minutes
    is_used = Column(Boolean, default=False, nullable=False)  # Prevent replay attacks
    
    def __repr__(self):
        return f"<OAuthSession(state={self.state[:10]}..., provider={self.provider})>"
