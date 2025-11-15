"""User profile and history endpoints."""
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Path, Query

from src.agents.personalization import PersonalizationAgent
from src.memory.memory_manager import MemoryManager
from ..schemas import (
    DraftHistoryResponse,
    LearnFromEditsRequest,
    UserProfile,
    UserProfileUpdate,
)

router = APIRouter()

_memory_manager = MemoryManager()
try:
    _personalizer: Optional[PersonalizationAgent] = PersonalizationAgent(llm=None)  # type: ignore[arg-type]
except Exception:  # pragma: no cover - fallback when LLM deps missing
    _personalizer = None

DEFAULT_PROFILE: Dict[str, Any] = {
    "user_name": "",
    "user_title": "",
    "user_company": "",
    "signature": "\n\nBest regards",
    "style_notes": "professional and clear",
    "preferences": {},
    "learned_preferences": {},
}


def _merge_profile(base: Dict[str, Any], updates: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data = {**DEFAULT_PROFILE, **(base or {})}
    if updates:
        data.update(updates)
    return data


def _load_profile(user_id: str) -> Dict[str, Any]:
    profile = _memory_manager.load_profile(user_id)
    if profile:
        return _merge_profile(profile)
    if _personalizer:
        return _merge_profile(_personalizer.get_profile(user_id))
    return DEFAULT_PROFILE.copy()


def _sync_personalizer_profile(user_id: str, profile: Dict[str, Any]) -> None:
    if not _personalizer:
        return
    try:
        _personalizer.save_profile(user_id, profile)
    except Exception:
        pass


@router.get("/{user_id}/profile", response_model=UserProfile)
async def get_user_profile(user_id: str = Path(..., description="Identifier for the user")) -> UserProfile:
    data = _load_profile(user_id)
    return UserProfile(user_id=user_id, **data)


@router.put("/{user_id}/profile", response_model=UserProfile)
async def update_user_profile(
    payload: UserProfileUpdate,
    user_id: str = Path(..., description="Identifier for the user"),
) -> UserProfile:
    existing = _load_profile(user_id)
    updates = payload.model_dump(exclude_none=True, exclude_unset=True)
    if not updates:
        return UserProfile(user_id=user_id, **existing)

    merged = _merge_profile(existing, updates)
    try:
        _memory_manager.save_profile(user_id, merged)
        _sync_personalizer_profile(user_id, merged)
    except Exception as exc:  # pragma: no cover - filesystem errors
        raise HTTPException(status_code=500, detail=f"Failed to save profile: {exc}") from exc

    return UserProfile(user_id=user_id, **merged)


@router.get("/{user_id}/history", response_model=DraftHistoryResponse)
async def get_user_history(
    user_id: str = Path(..., description="Identifier for the user"),
    limit: int = Query(20, ge=1, le=100, description="Maximum drafts to return"),
) -> DraftHistoryResponse:
    drafts = _memory_manager.get_draft_history(user_id, limit=limit)
    return DraftHistoryResponse(drafts=drafts)


@router.post("/{user_id}/history/learn")
async def learn_from_edits(
    payload: LearnFromEditsRequest,
    user_id: str = Path(..., description="Identifier for the user"),
) -> Dict[str, str]:
    _memory_manager.learn_from_edits(user_id, payload.original, payload.edited)
    profile = _memory_manager.load_profile(user_id)
    if profile:
        _sync_personalizer_profile(user_id, _merge_profile(profile))
    return {"status": "ok"}
