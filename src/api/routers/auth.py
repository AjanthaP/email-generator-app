"""OAuth session endpoints for the SPA."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from src.auth.oauth_providers import OAuthManager, create_oauth_manager
from src.memory.memory_manager import MemoryManager
from src.utils.config import settings
from ..schemas import (
	OAuthCallbackResponse,
	OAuthStartRequest,
	OAuthStartResponse,
	OAuthExchangeRequest,
)

router = APIRouter()

_oauth_manager: Optional[OAuthManager] = create_oauth_manager()
_memory_manager = MemoryManager()


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


def _complete_oauth_common(provider: str, code: str, state: str) -> OAuthCallbackResponse:
	manager = _ensure_manager()
	result = manager.complete_oauth_flow(provider, code=code, state=state)
	if not result:
		raise HTTPException(status_code=400, detail="OAuth completion failed")

	# Auto-create profile with OAuth data if it doesn't exist
	user_id = result.get('user_id')
	user_info = result.get('user_info', {})
	if user_id and user_info:
		existing_profile = _memory_manager.load_profile(user_id)
		if not existing_profile:
			# Extract company from email domain (e.g., user@acme.com -> Acme)
			company = ""
			email = user_info.get('email', '')
			if email and '@' in email:
				domain = email.split('@')[1]
				if '.' in domain:
					company_name = domain.split('.')[0]
					company = company_name.capitalize()

			# Create initial profile from OAuth data
			initial_profile: Dict[str, Any] = {
				"user_name": user_info.get('name', ''),
				"user_title": "",  # User can fill this in
				"user_company": company,
				"signature": "\n\nBest regards",
				"style_notes": "professional and clear",
				"preferences": {},
				"learned_preferences": {},
			}
			try:
				_memory_manager.save_profile(user_id, initial_profile)
			except Exception as e:
				print(f"Warning: Failed to auto-create profile for {user_id}: {e}")

	return OAuthCallbackResponse(**result)


@router.get("/callback", response_model=OAuthCallbackResponse)
async def complete_oauth(
	provider: str = Query(..., description="OAuth provider name"),
	code: str = Query(..., description="Authorization code returned by the provider"),
	state: str = Query(..., description="Opaque state returned by the provider"),
) -> OAuthCallbackResponse:
	return _complete_oauth_common(provider, code, state)


@router.get("/callback/{provider}", response_model=OAuthCallbackResponse)
async def complete_oauth_path(
	provider: str,
	code: str = Query(..., description="Authorization code returned by the provider"),
	state: str = Query(..., description="Opaque state returned by the provider"),
) -> OAuthCallbackResponse:
	"""Provider-specific callback path variant for providers that require fixed URIs.

	Example: /api/auth/callback/google?code=...&state=...
	"""
	return _complete_oauth_common(provider, code, state)


@router.post("/exchange", response_model=OAuthCallbackResponse)
async def exchange_oauth(request: OAuthExchangeRequest) -> OAuthCallbackResponse:
	"""CORS-friendly code exchange endpoint for SPAs.

	Frontends should navigate users to the provider authorization URL using
	`/api/auth/start`, and then either:
	- Let the provider redirect to `/api/auth/callback` (top-level navigation), or
	- Capture `code` and `state` in the frontend and call this endpoint via POST
	  to complete the exchange and receive JSON (no redirects).
	"""
	manager = _ensure_manager()
	result = manager.complete_oauth_flow(
		request.provider, code=request.code, state=request.state
	)
	if not result:
		raise HTTPException(status_code=400, detail="OAuth code exchange failed")

	# Optionally auto-create profile as done in the callback flow
	user_id = result.get('user_id')
	user_info = result.get('user_info', {})
	if user_id and user_info:
		existing_profile = _memory_manager.load_profile(user_id)
		if not existing_profile:
			company = ""
			email = user_info.get('email', '')
			if email and '@' in email:
				domain = email.split('@')[1]
				if '.' in domain:
					company_name = domain.split('.')[0]
					company = company_name.capitalize()
			initial_profile: Dict[str, Any] = {
				"user_name": user_info.get('name', ''),
				"user_title": "",
				"user_company": company,
				"signature": "\n\nBest regards",
				"style_notes": "professional and clear",
				"preferences": {},
				"learned_preferences": {},
			}
			try:
				_memory_manager.save_profile(user_id, initial_profile)
			except Exception as e:
				print(f"Warning: Failed to auto-create profile for {user_id}: {e}")

	return OAuthCallbackResponse(**result)


@router.post("/logout")
async def logout() -> Dict[str, str]:
	# Stateless placeholder for parity with future session management.
	return {"status": "ok"}
