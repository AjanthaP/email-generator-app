"""Chroma vector store wrapper for draft history similarity search.

Provides async indexing on draft saves and top-k retrieval per user.
"""
from __future__ import annotations

import os
import threading
import logging
from typing import Any, Dict, List, Optional

from src.utils.config import settings

try:
    import chromadb
    from chromadb.utils import embedding_functions
except Exception as e:  # pragma: no cover - optional import safety
    chromadb = None  # type: ignore
    embedding_functions = None  # type: ignore

logger = logging.getLogger(__name__)


class GeminiEmbeddingFunction:
    """Embedding function using Google Generative AI embeddings.

    Falls back to Chroma's DefaultEmbeddingFunction if Gemini is unavailable
    or disabled via settings.
    """

    def __init__(self, model: str = "models/text-embedding-004") -> None:
        self.model = model
        self._fallback = None

        # Lazy import to avoid hard dependency if not used
        try:
            import google.generativeai as genai  # type: ignore

            if settings.gemini_api_key and not settings.donotusegemini:
                genai.configure(api_key=settings.gemini_api_key)
                self._genai = genai
            else:
                raise RuntimeError("Gemini API key missing or disabled by settings")
        except Exception as e:  # pragma: no cover - environment dependent
            logger.warning(
                f"Gemini embeddings not available ({e}); using default embedding function if possible"
            )
            self._genai = None
            # Fallback to Chroma default embedding if available
            if embedding_functions is not None:
                try:
                    self._fallback = embedding_functions.DefaultEmbeddingFunction()
                except Exception:
                    self._fallback = None

    def __call__(self, texts: List[str]) -> List[List[float]]:  # type: ignore[override]
        if not isinstance(texts, list):
            texts = [texts]

        # Prefer Gemini embeddings if configured
        if getattr(self, "_genai", None):
            out: List[List[float]] = []
            for t in texts:
                try:
                    resp = self._genai.embed_content(model=self.model, content=t, task_type="retrieval_document")
                    vec = resp["embedding"] if isinstance(resp, dict) else getattr(resp, "embedding", None)
                    if not vec:
                        raise RuntimeError("Empty embedding from Gemini")
                    out.append(vec)
                except Exception as e:  # pragma: no cover - network dependent
                    logger.debug(f"Gemini embedding failed for text length {len(t)}: {e}")
                    out.append([0.0])  # keep shape; will be ignored by ANN
            return out

        # Fallback embedding if available
        if self._fallback is not None:
            try:
                return self._fallback(texts)
            except Exception as e:  # pragma: no cover
                logger.debug(f"Default embedding failed: {e}")

        # Last-resort deterministic pseudo-vector (very weak; avoids crashes)
        return [[float((hash(t) % 1000) / 1000.0)] for t in texts]


class ChromaVectorStore:
    """Light wrapper around Chroma for per-user draft indexing and search."""

    def __init__(self) -> None:
        if chromadb is None:
            raise RuntimeError("chromadb is not installed; cannot initialize vector store")

        client: Any
        if settings.chromadb_use_server:
            client = chromadb.HttpClient(
                host=settings.chromadb_host,
                port=settings.chromadb_port,
                settings=chromadb.config.Settings(
                    anonymized_telemetry=settings.chromadb_anonymized_telemetry
                ),
            )
        else:
            os.makedirs(settings.chromadb_persist_dir, exist_ok=True)
            client = chromadb.PersistentClient(
                path=settings.chromadb_persist_dir,
                settings=chromadb.config.Settings(
                    anonymized_telemetry=settings.chromadb_anonymized_telemetry
                ),
            )

        self.client = client
        self.embedding_fn = GeminiEmbeddingFunction()
        # Create/get a single collection; filter by user_id per query
        self.collection = self.client.get_or_create_collection(
            name=settings.chromadb_collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_draft(
        self,
        user_id: str,
        draft_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not settings.enable_chromadb:
            return
        if not content or not user_id or not draft_id:
            return
        meta = {"user_id": user_id, **(metadata or {})}
        # Use composite id to keep uniqueness across users
        uid = f"{user_id}:{draft_id}"
        try:
            self.collection.upsert(
                ids=[uid],
                documents=[content],
                metadatas=[meta],
            )
            logger.debug(f"Upserted draft into Chroma (user={user_id}, id={draft_id})")
        except Exception as e:  # pragma: no cover - depends on environment
            logger.warning(f"Chroma upsert failed for user={user_id}, id={draft_id}: {e}")

    def query_similar(
        self,
        user_id: str,
        query_text: str,
        k: int = 3,
    ) -> List[Dict[str, Any]]:
        if not settings.enable_chromadb:
            return []
        if not query_text:
            return []
        try:
            results = self.collection.query(
                query_texts=[query_text],
                where={"user_id": user_id},
                n_results=max(1, min(k, 10)),
            )
            # Normalize output
            docs = results.get("documents", [[]])[0] if isinstance(results, dict) else []
            metas = results.get("metadatas", [[]])[0] if isinstance(results, dict) else []
            dists = results.get("distances", [[]])[0] if isinstance(results, dict) else []
            items: List[Dict[str, Any]] = []
            for i, doc in enumerate(docs):
                items.append(
                    {
                        "content": doc,
                        "metadata": metas[i] if i < len(metas) else {},
                        "distance": dists[i] if i < len(dists) else None,
                    }
                )
            return items
        except Exception as e:  # pragma: no cover
            logger.warning(f"Chroma query failed for user={user_id}: {e}")
            return []


_store: Optional[ChromaVectorStore] = None
_index_executor_lock = threading.Lock()


def get_vector_store() -> Optional[ChromaVectorStore]:
    global _store
    if not settings.enable_chromadb:
        return None
    if _store is None:
        try:
            _store = ChromaVectorStore()
        except Exception as e:  # pragma: no cover - environment dependent
            logger.warning(f"Vector store initialization failed: {e}")
            _store = None
    return _store


def index_draft_async(user_id: str, draft_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """Index a draft in the background to avoid blocking request handlers."""
    if not settings.enable_chromadb:
        return

    store = get_vector_store()
    if store is None:
        return

    def _task():
        try:
            store.upsert_draft(user_id=user_id, draft_id=draft_id, content=content, metadata=metadata)
        except Exception as e:  # pragma: no cover
            logger.debug(f"Background indexing failed for user={user_id}, id={draft_id}: {e}")

    # Fire-and-forget thread
    t = threading.Thread(target=_task, name=f"chroma-index-{user_id}-{draft_id}")
    t.daemon = True
    t.start()
