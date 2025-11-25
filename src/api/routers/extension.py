"""Extension-specific API endpoints for browser extension integration.

Staging version: Simplified auth (API key in header), reduced payload schema.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Depends
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from src.workflow.langgraph_flow import execute_workflow
from src.utils.config import settings

router = APIRouter(prefix="/extension", tags=["extension"])


# Staging: Simple API key validation (replace with DB lookup in production)
STAGING_API_KEYS = {
    "demo-key-001": {"user_id": "extension-demo-user", "plan": "free"},
    "test-key-staging": {"user_id": "staging-tester", "plan": "unlimited"}
}


async def validate_api_key(x_extension_key: Optional[str] = Header(None)) -> dict:
    """Validate extension API key from header.
    
    Staging: In-memory key store. Production: DB lookup with bcrypt.
    """
    if not x_extension_key:
        raise HTTPException(status_code=401, detail="Missing X-Extension-Key header")
    
    key_data = STAGING_API_KEYS.get(x_extension_key)
    if not key_data:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return key_data


class ExtensionGenerateRequest(BaseModel):
    """Simplified schema for extension requests."""
    recipient: Optional[str] = Field(None, description="Recipient email or name")
    subject: Optional[str] = Field(None, description="Email subject line")
    body_context: Optional[str] = Field(None, description="Existing body text or notes")
    tone: str = Field("professional", description="Tone: professional, friendly, formal, casual")
    length_preference: Optional[int] = Field(None, description="Target word count (default: workflow decides)")
    sender_email: Optional[str] = Field(None, description="Logged-in user email from Gmail/Outlook")
    sender_name: Optional[str] = Field(None, description="User's full name from OAuth profile")
    signature: Optional[str] = Field(None, description="User's email signature extracted from compose")


class ExtensionGenerateResponse(BaseModel):
    """Streamlined response for extension."""
    draft: str
    word_count: int
    tone: str
    intent: Optional[str] = None
    similar_used: int = Field(0, description="Number of similar past drafts used for personalization")
    metadata: dict = Field(default_factory=dict)


@router.post("/generate", response_model=ExtensionGenerateResponse)
async def extension_generate(
    payload: ExtensionGenerateRequest,
    key_data: dict = Depends(validate_api_key)
) -> ExtensionGenerateResponse:
    """Generate email draft from extension context.
    
    Flow:
    1. Build prompt from recipient + subject + body_context
    2. Call existing workflow
    3. Return slim response
    """
    user_id = key_data["user_id"]
    
    # Build prompt from extension context
    prompt_parts = []
    if payload.recipient:
        prompt_parts.append(f"Recipient: {payload.recipient}")
    if payload.subject:
        prompt_parts.append(f"Subject: {payload.subject}")
    if payload.body_context:
        prompt_parts.append(f"Context/Notes: {payload.body_context}")
    
    if not prompt_parts:
        raise HTTPException(status_code=400, detail="Must provide at least one of: recipient, subject, or body_context")
    
    full_prompt = "\n\n".join(prompt_parts)
    
    # Override user_id with sender email if provided (better personalization)
    effective_user_id = payload.sender_email if payload.sender_email else user_id
    
    # If signature provided, update user profile dynamically
    if (payload.signature or payload.sender_name) and effective_user_id:
        try:
            from src.memory.memory_manager import memory_manager
            # Get or create profile
            profile = memory_manager.get_user_profile(effective_user_id) or {}
            
            # Update name if provided from OAuth
            if payload.sender_name and not profile.get('name'):
                profile['name'] = payload.sender_name
            
            # Update signature if provided and different
            if payload.signature and profile.get('signature') != payload.signature:
                profile['signature'] = payload.signature
                # Extract name from signature if still not set
                if not profile.get('name'):
                    sig_lines = payload.signature.split('\n')
                    for line in sig_lines[1:4]:  # Skip first line, check next 2-3
                        clean_line = line.strip()
                        if clean_line and len(clean_line) < 50 and '@' not in clean_line:
                            profile['name'] = clean_line
                            break
            
            memory_manager.save_user_profile(effective_user_id, profile)
        except Exception as e:
            # Don't fail request if profile update fails
            print(f"[Extension] Warning: Could not update profile: {e}")
    
    try:
        # Call existing workflow
        state = await run_in_threadpool(
            execute_workflow,
            full_prompt,
            use_stub=False,
            user_id=effective_user_id,
            tone=payload.tone,
            developer_mode=False,
            length_preference=payload.length_preference,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Draft generation failed: {exc}")
    
    # Extract draft
    draft = (
        state.get("final_draft")
        or state.get("personalized_draft")
        or state.get("styled_draft")
        or state.get("draft")
    )
    
    if not draft:
        raise HTTPException(status_code=502, detail="Workflow returned no draft")
    
    metadata = state.get("metadata", {})
    
    return ExtensionGenerateResponse(
        draft=draft,
        word_count=len(draft.split()),
        tone=payload.tone,
        intent=state.get("intent"),
        similar_used=metadata.get("similar_drafts_count", 0),
        metadata={
            "model": metadata.get("model"),
            "source": metadata.get("source", "llm"),
        }
    )


class ExtensionUsageResponse(BaseModel):
    """Usage stats for extension user."""
    user_id: str
    plan: str
    drafts_today: int = 0
    quota_remaining: Optional[int] = None


@router.get("/usage", response_model=ExtensionUsageResponse)
async def extension_usage(key_data: dict = Depends(validate_api_key)) -> ExtensionUsageResponse:
    """Return usage stats for current API key.
    
    Staging: Mock data. Production: Query DB.
    """
    return ExtensionUsageResponse(
        user_id=key_data["user_id"],
        plan=key_data["plan"],
        drafts_today=0,  # Staging: no tracking yet
        quota_remaining=None if key_data["plan"] == "unlimited" else 50
    )


@router.get("/health")
async def extension_health() -> dict:
    """Health check endpoint for extension to verify API availability."""
    return {
        "status": "ok",
        "service": "email-generator-extension-api",
        "version": "0.1.0-staging"
    }
