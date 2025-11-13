from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EmailGenerateRequest(BaseModel):
    prompt: str = Field(..., description="Natural language description of the desired email")
    user_id: str = Field("default", description="Identifier used for personalization and history")
    tone: Optional[str] = Field(
        default=None,
        description="Preferred tone for the email (e.g., formal, casual)"
    )
    recipient: Optional[str] = Field(default=None, description="Recipient name")
    recipient_email: Optional[str] = Field(default=None, description="Recipient email address")
    length_preference: Optional[int] = Field(
        default=None,
        ge=50,
        le=1500,
        description="Approximate preferred length in words"
    )
    save_to_history: bool = Field(
        default=True,
        description="Whether to persist the generated draft in user history"
    )
    use_stub: bool = Field(
        default=False,
        description="If true, run the stub workflow instead of calling the LLM"
    )
    reset_context: bool = Field(
        default=False,
        description="If true, clear stored history before running the workflow"
    )


class EmailGenerateResponse(BaseModel):
    draft: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    review_notes: Dict[str, Any] = Field(default_factory=dict)
    saved: bool = Field(default=False, description="Whether the draft was persisted to history")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Aggregated usage metrics")
    context_mode: str = Field(
        default="contextual",
        description="Indicates whether the draft used prior context or started fresh",
    )


class HealthCheckResponse(BaseModel):
    status: str = "ok"
    app_name: str
    version: str


class OAuthStartRequest(BaseModel):
    provider: str = Field(..., description="OAuth provider name (google, github, etc.)")
    user_id: Optional[str] = Field(
        default=None,
        description="Optional user identifier for associating the OAuth session",
    )


class OAuthStartResponse(BaseModel):
    authorization_url: str
    state: str
    session_id: Optional[str] = None
    provider: str


class OAuthCallbackResponse(BaseModel):
    session_id: str
    provider: str
    user_id: Optional[str] = None
    user_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="User information from OAuth provider (email, name, etc.)",
    )
    tokens: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw provider token payload (access_token, refresh_token, expires_in, etc.)",
    )


class OAuthExchangeRequest(BaseModel):
    provider: str = Field(..., description="OAuth provider name (google, github, microsoft)")
    code: str = Field(..., description="Authorization code returned by the provider")
    state: str = Field(..., description="Opaque state returned by the provider")


class UserProfile(BaseModel):
    user_id: str
    user_name: str = ""
    user_title: str = ""
    user_company: str = ""
    signature: str = "\n\nBest regards"
    style_notes: str = "professional and clear"
    preferences: Dict[str, Any] = Field(default_factory=dict)
    learned_preferences: Dict[str, Any] = Field(default_factory=dict)


class UserProfileUpdate(BaseModel):
    user_name: Optional[str] = None
    user_title: Optional[str] = None
    user_company: Optional[str] = None
    signature: Optional[str] = None
    style_notes: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    learned_preferences: Optional[Dict[str, Any]] = None


class DraftHistoryResponse(BaseModel):
    drafts: List[Dict[str, Any]] = Field(default_factory=list)


class LearnFromEditsRequest(BaseModel):
    original: str = Field(..., description="Original draft content before edits")
    edited: str = Field(..., description="Edited draft content provided by the user")
