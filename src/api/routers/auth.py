"""OAuth session endpoints for the SPA."""
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from src.auth.oauth_providers import OAuthManager, create_oauth_manager
from src.utils.config import settings
from ..schemas import OAuthCallbackResponse, OAuthStartRequest, OAuthStartResponse

router = APIRouter()

_oauth_manager: Optional[OAuthManager] = create_oauth_manager()


def _ensure_manager() -> OAuthManager:
	"""Verify OAuth is configured before serving requests."""
	if not settings.enable_oauth or settings.disable_oauth:
		raise HTTPException(status_code=503, detail="OAuth is disabled")
	if _oauth_manager is None or not _oauth_manager.providers:
		raise HTTPException(status_code=503, detail="No OAuth providers are configured")
	return _oauth_manager


@router.get("/providers", response_model=List[str])
async def list_providers() -> List[str]:
	manager = _ensure_manager()
	return manager.get_available_providers()


@router.post("/start", response_model=OAuthStartResponse)
async def start_oauth(request: OAuthStartRequest) -> OAuthStartResponse:
	manager = _ensure_manager()
	result = manager.start_oauth_flow(request.provider, user_id=request.user_id)
	if not result:
		raise HTTPException(status_code=400, detail="Unable to start OAuth flow")
	return OAuthStartResponse(**result)


@router.get("/callback", response_model=OAuthCallbackResponse)
async def complete_oauth(
	provider: str = Query(..., description="OAuth provider name"),
	code: str = Query(..., description="Authorization code returned by the provider"),
	state: str = Query(..., description="Opaque state returned by the provider"),
) -> OAuthCallbackResponse:
	manager = _ensure_manager()
	result = manager.complete_oauth_flow(provider, code=code, state=state)
	if not result:
		raise HTTPException(status_code=400, detail="OAuth completion failed")
	return OAuthCallbackResponse(**result)


@router.post("/logout")
async def logout() -> Dict[str, str]:
	# Stateless placeholder for parity with future session management.
	return {"status": "ok"}
