"""FastAPI backend for the AI Email Assistant.

This service exposes REST endpoints that wrap the LangGraph workflow, making it
accessible to external clients (e.g., a React front-end).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.utils.config import settings
from .routers import auth, email, users
from .schemas import HealthCheckResponse

app = FastAPI(title=settings.app_name, version="1.0.0")

# Configure CORS using existing settings to share cookies/bearer tokens later.
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Lightweight readiness endpoint for monitoring."""
    return HealthCheckResponse(app_name=settings.app_name)


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(email.router, prefix="/api/v1/email", tags=["email"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])


# Entrypoint hint for `uvicorn src.api.main:app --reload`
__all__ = ["app"]
