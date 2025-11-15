"""OAuth session endpoints for the SPA."""
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

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


def _get_db_session():
	"""Get a SQLAlchemy session, lazily initializing the DB if needed."""
	try:
		from src.db.database import get_db_manager
		try:
			db_manager = get_db_manager()
		except RuntimeError:
			from src.db.database import init_db
			db_manager = init_db()
		return db_manager.get_session()
	except Exception:
		return None


def _ensure_manager() -> OAuthManager:
	"""Verify OAuth is configured before serving requests."""
	# Enable-only flag convention: if enable_oauth is False treat as disabled
	if not settings.enable_oauth:
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

	# Persist OAuth session to DB (best-effort)
	try:
		db = _get_db_session()
		if db is not None:
			from src.db.models import OAuthSession
			# Determine redirect URI used by provider
			redirect_uri = None
			try:
				provider_obj = _oauth_manager.providers.get(request.provider) if _oauth_manager else None
				redirect_uri = getattr(provider_obj, "redirect_uri", None)
			except Exception:
				redirect_uri = None

			expires_at = datetime.utcnow() + timedelta(minutes=10)
			session_row = OAuthSession(
				state=result["state"],
				provider=request.provider,
				redirect_uri=redirect_uri or settings.google_redirect_uri,
				code_verifier=None,
				expires_at=expires_at,
				is_used=False,
			)
			# Upsert-like behavior: ignore if already exists
			existing = db.query(OAuthSession).filter_by(state=result["state"]).first()
			if not existing:
				db.add(session_row)
			db.commit()
			db.close()
	except Exception:
		# Non-fatal: do not block auth if persistence fails
		pass

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
				print(f"[OAuth] Creating profile for user {user_id} with name: {initial_profile['user_name']}")
				_memory_manager.save_profile(user_id, initial_profile)
				print(f"[OAuth] Profile created successfully for {user_id}")
			except Exception as e:
				print(f"[OAuth] ERROR: Failed to auto-create profile for {user_id}: {e}")
				import traceback
				traceback.print_exc()

		# Update last_login_at and provider linkage
		try:
			db = _get_db_session()
			if db is not None:
				from src.db.models import UserProfile, OAuthSession
				profile_row = db.query(UserProfile).filter_by(id=user_id).first()
				if profile_row:
					profile_row.last_login_at = datetime.utcnow()
					profile_row.oauth_provider = profile_row.oauth_provider or provider
					# Attempt to store provider user id if available
					prov_uid = user_info.get("provider_id") or user_info.get("id")
					if prov_uid and not profile_row.oauth_user_id:
						profile_row.oauth_user_id = str(prov_uid)
				# Mark OAuth session as used
				sess = db.query(OAuthSession).filter_by(state=state).first()
				if sess and not sess.is_used:
					sess.is_used = True
				db.commit()
				db.close()
		except Exception:
			pass

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
	try:
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
			try:
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
					print(f"[OAuth/Exchange] Creating profile for user {user_id} with name: {initial_profile['user_name']}")
					_memory_manager.save_profile(user_id, initial_profile)
					print(f"[OAuth/Exchange] Profile created successfully for {user_id}")
			except Exception as e:
				print(f"[OAuth/Exchange] ERROR: Failed to auto-create profile for {user_id}: {e}")
				import traceback
				traceback.print_exc()
				# Continue even if profile creation fails

			# Update last_login_at and mark OAuth session used
			try:
				db = _get_db_session()
				if db is not None:
					from src.db.models import UserProfile, OAuthSession
					profile_row = db.query(UserProfile).filter_by(id=user_id).first()
					if profile_row:
						profile_row.last_login_at = datetime.utcnow()
						profile_row.oauth_provider = profile_row.oauth_provider or request.provider
						prov_uid = user_info.get("provider_id") or user_info.get("id")
						if prov_uid and not profile_row.oauth_user_id:
							profile_row.oauth_user_id = str(prov_uid)
					sess = db.query(OAuthSession).filter_by(state=request.state).first()
					if sess and not sess.is_used:
						sess.is_used = True
					db.commit()
					db.close()
			except Exception:
				pass

		return OAuthCallbackResponse(**result)
	except HTTPException:
		raise
	except Exception as e:
		print(f"Error in exchange_oauth: {type(e).__name__}: {e}")
		raise HTTPException(status_code=500, detail=f"OAuth exchange failed: {str(e)}")


@router.post("/logout")
async def logout() -> Dict[str, str]:
	# Stateless placeholder for parity with future session management.
	return {"status": "ok"}
