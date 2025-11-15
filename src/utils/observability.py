"""Observability helpers: LangSmith activation and RunnableConfig builder.

This module centralizes tracing activation so the rest of the codebase can stay
clean. Importing this file is safe even if LangSmith isn't installed; it will
fail gracefully when dependencies or env vars are missing.
"""
from __future__ import annotations

import os
import logging
from typing import Dict, Any

from .config import settings

logger = logging.getLogger(__name__)

_LANGSMITH_ACTIVATED = False

def activate_langsmith() -> bool:
    """Activate LangSmith tracing if configured.

    Supports both personal and workspace-scoped API keys.
    If workspace ID is provided, it will be used; otherwise falls back to personal API.

    Returns True if activation steps executed (even if partial), False otherwise.
    """
    global _LANGSMITH_ACTIVATED
    if _LANGSMITH_ACTIVATED:
        return True

    if not settings.enable_langsmith:
        return False

    try:
        # Set environment variables expected by LangChain tracing V2
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        if settings.langsmith_api_key:
            os.environ.setdefault("LANGSMITH_API_KEY", settings.langsmith_api_key)
        if settings.langchain_project:
            os.environ.setdefault("LANGCHAIN_PROJECT", settings.langchain_project)
        
        # Workspace ID is optional - only set if provided (for org-scoped keys)
        # Personal API keys work without workspace ID
        if hasattr(settings, 'langsmith_workspace_id') and settings.langsmith_workspace_id:
            if settings.langsmith_workspace_id != "your_workspace_id_here":
                os.environ.setdefault("LANGSMITH_WORKSPACE_ID", settings.langsmith_workspace_id)
                logger.info("LangSmith tracing activated (project=%s, workspace=%s)", 
                           settings.langchain_project, settings.langsmith_workspace_id)
            else:
                logger.info("LangSmith tracing activated with personal API key (project=%s)", 
                           settings.langchain_project)
        else:
            logger.info("LangSmith tracing activated with personal API key (project=%s)", 
                       settings.langchain_project)
        
        _LANGSMITH_ACTIVATED = True
        return True
    except Exception:
        logger.exception("Failed to activate LangSmith tracing")
        return False


def build_runnable_config(tags: list[str] | None = None, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Return a RunnableConfig-like dict when tracing is active.

    This helper avoids importing langchain core types throughout the code.
    """
    if not _LANGSMITH_ACTIVATED:
        return {}

    cfg: Dict[str, Any] = {}
    if tags:
        cfg["tags"] = tags
    if metadata:
        cfg["metadata"] = metadata
    return cfg

__all__ = ["activate_langsmith", "build_runnable_config"]
