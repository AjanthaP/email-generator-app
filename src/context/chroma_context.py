"""
ChromaDB Context Manager for Email Generator App.

Provides vector-based storage for user context, conversation history,
and semantic search capabilities.
"""

import chromadb
from chromadb.config import Settings
import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
import os

try:
    from ..utils.config import settings as app_settings
except ImportError:
    # Fallback for when imported directly
    class MockSettings:
        enable_chromadb = True
        disable_chromadb = False
        chromadb_persist_dir = "data/chromadb"
        chromadb_collection_name = "email_contexts"
        chromadb_allow_reset = False
        chromadb_anonymized_telemetry = False
    app_settings = MockSettings()


class ChromaContextManager:
    """
    ChromaDB-based context manager for storing and retrieving user context.
    
    Features:
    - Conversation history storage with embeddings
    - Semantic search across user's email history
    - Context-aware email generation
    - User preference learning
    - Similar email retrieval
    """
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        """
        Initialize ChromaDB context manager.
        
        Args:
            persist_directory: Directory to persist ChromaDB data (uses config if None)
            collection_name: Name of the collection to store contexts (uses config if None)
        """
        # Use settings from config with parameter overrides
        self.persist_directory = persist_directory or app_settings.chromadb_persist_dir
        self.collection_name = collection_name or app_settings.chromadb_collection_name
        self.use_server = app_settings.chromadb_use_server
        self.host = app_settings.chromadb_host
        self.port = app_settings.chromadb_port
        
        # Initialize ChromaDB client based on mode
        if self.use_server:
            # Server/Client mode
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(
                    anonymized_telemetry=app_settings.chromadb_anonymized_telemetry,
                    allow_reset=app_settings.chromadb_allow_reset
                )
            )
        else:
            # Persistent local mode
            # Ensure directory exists
            os.makedirs(self.persist_directory, exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=app_settings.chromadb_anonymized_telemetry,
                    allow_reset=app_settings.chromadb_allow_reset
                )
            )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(collection_name)
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Email generation contexts and history"}
            )
    
    def _generate_doc_id(self, user_id: str, content_type: str, timestamp: str = None) -> str:
        """Generate unique document ID."""
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        
        content_hash = hashlib.md5(f"{user_id}_{content_type}_{timestamp}".encode()).hexdigest()
        return f"{user_id}_{content_type}_{content_hash[:8]}"
    
    def store_email_context(
        self,
        user_id: str,
        email_content: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Store email context in ChromaDB.
        
        Args:
            user_id: User identifier
            email_content: The email content/draft
            metadata: Additional metadata (intent, recipient, tone, etc.)
            
        Returns:
            Document ID of stored context
        """
        doc_id = self._generate_doc_id(user_id, "email")
        timestamp = datetime.utcnow().isoformat()
        
        # Prepare metadata
        full_metadata = {
            "user_id": user_id,
            "type": "email",
            "timestamp": timestamp,
            "content_length": len(email_content),
            **metadata
        }
        
        # Store in ChromaDB
        self.collection.add(
            documents=[email_content],
            metadatas=[full_metadata],
            ids=[doc_id]
        )
        
        return doc_id
    
    def store_conversation_context(
        self,
        user_id: str,
        conversation: List[Dict],
        session_id: str = None
    ) -> str:
        """
        Store conversation context.
        
        Args:
            user_id: User identifier
            conversation: List of conversation turns
            session_id: Optional session identifier
            
        Returns:
            Document ID of stored context
        """
        doc_id = self._generate_doc_id(user_id, "conversation")
        timestamp = datetime.utcnow().isoformat()
        
        # Convert conversation to searchable text
        conversation_text = "\n".join([
            f"{turn.get('role', 'user')}: {turn.get('content', '')}"
            for turn in conversation
        ])
        
        metadata = {
            "user_id": user_id,
            "type": "conversation",
            "timestamp": timestamp,
            "session_id": session_id or "unknown",
            "turn_count": len(conversation),
            "content_length": len(conversation_text)
        }
        
        self.collection.add(
            documents=[conversation_text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        return doc_id
    
    def store_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> str:
        """
        Store user preferences and learned patterns.
        
        Args:
            user_id: User identifier
            preferences: User preferences dict
            
        Returns:
            Document ID of stored preferences
        """
        doc_id = f"{user_id}_preferences"
        timestamp = datetime.utcnow().isoformat()
        
        # Convert preferences to searchable text
        pref_text = json.dumps(preferences, indent=2)
        
        metadata = {
            "user_id": user_id,
            "type": "preferences",
            "timestamp": timestamp,
            "preference_count": len(preferences)
        }
        
        # Upsert preferences (update if exists)
        try:
            # Try to update existing
            self.collection.update(
                documents=[pref_text],
                metadatas=[metadata],
                ids=[doc_id]
            )
        except Exception:
            # Create new if doesn't exist
            self.collection.add(
                documents=[pref_text],
                metadatas=[metadata],
                ids=[doc_id]
            )
        
        return doc_id
    
    def get_similar_emails(
        self,
        user_id: str,
        query_text: str,
        limit: int = 5,
        min_similarity: float = 0.7
    ) -> List[Dict]:
        """
        Find similar emails for the user based on content.
        
        Args:
            user_id: User identifier
            query_text: Text to find similar content for
            limit: Maximum number of results
            min_similarity: Minimum similarity score (0-1)
            
        Returns:
            List of similar email contexts
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=limit,
                where={"user_id": user_id, "type": "email"},
                include=["documents", "metadatas", "distances"]
            )
            
            similar_emails = []
            
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )):
                    # Convert distance to similarity (ChromaDB uses cosine distance)
                    similarity = 1 - distance
                    
                    if similarity >= min_similarity:
                        similar_emails.append({
                            "content": doc,
                            "metadata": metadata,
                            "similarity": similarity,
                            "rank": i + 1
                        })
            
            return similar_emails
        except Exception as e:
            print(f"Error finding similar emails: {e}")
            return []
    
    def get_user_context_summary(
        self,
        user_id: str,
        context_types: List[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get summary of user's context over time.
        
        Args:
            user_id: User identifier
            context_types: Types of context to include (email, conversation, preferences)
            days_back: Number of days to look back
            
        Returns:
            Context summary dict
        """
        if context_types is None:
            context_types = ["email", "conversation", "preferences"]
        
        # Calculate date threshold
        from datetime import timedelta
        threshold_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
        
        summary = {
            "user_id": user_id,
            "summary_date": datetime.utcnow().isoformat(),
            "days_back": days_back,
            "context_counts": {},
            "recent_patterns": {}
        }
        
        for context_type in context_types:
            try:
                # Get documents of this type for the user
                results = self.collection.get(
                    where={
                        "user_id": user_id,
                        "type": context_type,
                        "timestamp": {"$gte": threshold_date}
                    },
                    include=["metadatas"]
                )
                
                count = len(results["metadatas"]) if results["metadatas"] else 0
                summary["context_counts"][context_type] = count
                
                # Extract patterns from metadata
                if results["metadatas"]:
                    patterns = {}
                    for metadata in results["metadatas"]:
                        for key, value in metadata.items():
                            if key not in ["user_id", "type", "timestamp", "content_length"]:
                                if key not in patterns:
                                    patterns[key] = {}
                                
                                value_str = str(value)
                                patterns[key][value_str] = patterns[key].get(value_str, 0) + 1
                    
                    summary["recent_patterns"][context_type] = patterns
            
            except Exception as e:
                print(f"Error analyzing {context_type} context: {e}")
                summary["context_counts"][context_type] = 0
                summary["recent_patterns"][context_type] = {}
        
        return summary
    
    def get_contextual_suggestions(
        self,
        user_id: str,
        current_prompt: str,
        suggestion_types: List[str] = None
    ) -> Dict[str, List[str]]:
        """
        Get contextual suggestions based on user's history.
        
        Args:
            user_id: User identifier
            current_prompt: Current email prompt
            suggestion_types: Types of suggestions to generate
            
        Returns:
            Dict of suggestion types and their values
        """
        if suggestion_types is None:
            suggestion_types = ["recipients", "tones", "intents", "phrases"]
        
        suggestions = {}
        
        # Find similar past emails
        similar_emails = self.get_similar_emails(user_id, current_prompt, limit=10)
        
        for suggestion_type in suggestion_types:
            suggestions[suggestion_type] = []
            
            if suggestion_type == "recipients":
                recipients = set()
                for email in similar_emails:
                    recipient = email["metadata"].get("recipient")
                    if recipient:
                        recipients.add(recipient)
                suggestions[suggestion_type] = list(recipients)[:5]
            
            elif suggestion_type == "tones":
                tones = {}
                for email in similar_emails:
                    tone = email["metadata"].get("tone")
                    if tone:
                        tones[tone] = tones.get(tone, 0) + 1
                # Sort by frequency
                suggestions[suggestion_type] = [
                    tone for tone, _ in sorted(tones.items(), key=lambda x: x[1], reverse=True)
                ][:3]
            
            elif suggestion_type == "intents":
                intents = {}
                for email in similar_emails:
                    intent = email["metadata"].get("intent")
                    if intent:
                        intents[intent] = intents.get(intent, 0) + 1
                suggestions[suggestion_type] = [
                    intent for intent, _ in sorted(intents.items(), key=lambda x: x[1], reverse=True)
                ][:3]
            
            elif suggestion_type == "phrases":
                # Extract common phrases from similar emails
                phrases = set()
                for email in similar_emails:
                    content = email["content"]
                    # Simple phrase extraction (could be more sophisticated)
                    sentences = content.split(".")
                    for sentence in sentences[:3]:  # First few sentences
                        sentence = sentence.strip()
                        if 20 <= len(sentence) <= 100:  # Reasonable phrase length
                            phrases.add(sentence)
                suggestions[suggestion_type] = list(phrases)[:5]
        
        return suggestions
    
    def delete_user_contexts(
        self,
        user_id: str,
        context_types: List[str] = None
    ) -> int:
        """
        Delete user contexts (for privacy/GDPR compliance).
        
        Args:
            user_id: User identifier
            context_types: Types of context to delete (None for all)
            
        Returns:
            Number of contexts deleted
        """
        try:
            where_clause = {"user_id": user_id}
            if context_types:
                where_clause["type"] = {"$in": context_types}
            
            # Get IDs to delete
            results = self.collection.get(
                where=where_clause,
                include=["metadatas"]
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                return len(results["ids"])
            
            return 0
        except Exception as e:
            print(f"Error deleting user contexts: {e}")
            return 0
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get ChromaDB collection statistics."""
        try:
            count = self.collection.count()
            
            # Get some sample metadata to understand distribution
            sample = self.collection.get(
                limit=min(100, count),
                include=["metadatas"]
            )
            
            user_counts = {}
            type_counts = {}
            
            if sample["metadatas"]:
                for metadata in sample["metadatas"]:
                    user_id = metadata.get("user_id", "unknown")
                    context_type = metadata.get("type", "unknown")
                    
                    user_counts[user_id] = user_counts.get(user_id, 0) + 1
                    type_counts[context_type] = type_counts.get(context_type, 0) + 1
            
            return {
                "total_documents": count,
                "unique_users": len(user_counts),
                "context_type_distribution": type_counts,
                "average_docs_per_user": count / max(len(user_counts), 1),
                "collection_name": self.collection_name
            }
        except Exception as e:
            return {"error": str(e)}


# Factory function
def create_chroma_context_manager(
    use_chromadb: Optional[bool] = None,
    persist_directory: Optional[str] = None,
    **kwargs
) -> Optional[ChromaContextManager]:
    """
    Factory function to create ChromaDB context manager.
    
    Args:
        use_chromadb: Whether to use ChromaDB (uses config if None)
        persist_directory: Directory for ChromaDB persistence (uses config if None)
        **kwargs: Additional ChromaDB parameters
        
    Returns:
        ChromaContextManager instance or None if disabled
    """
    # Use settings to determine if ChromaDB should be enabled
    use_chromadb = use_chromadb if use_chromadb is not None else app_settings.enable_chromadb
    
    # Check if ChromaDB is disabled via settings
    if not use_chromadb or app_settings.disable_chromadb:
        return None
    
    try:
        return ChromaContextManager(persist_directory=persist_directory, **kwargs)
    except Exception as e:
        print(f"Failed to initialize ChromaDB: {e}")
        return None