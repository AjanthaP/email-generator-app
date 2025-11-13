"""FastAPI backend for the AI Email Assistant.

This service exposes REST endpoints that wrap the LangGraph workflow, making it
accessible to external clients (e.g., a React front-end).
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.utils.config import settings
from .routers import auth, email, users
from .schemas import HealthCheckResponse

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI-Powered Email Generation API",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Configure CORS - allow configured origins plus common deployment env vars
origins = list(settings.cors_origins) if settings.cors_origins else [
    "http://localhost:5173",
    "http://localhost:3000",
]

# Include commonly used env vars for production frontends (Railway, Vercel, custom)
for var in [
    "RAILWAY_FRONTEND_URL",
    "FRONTEND_URL",
    "VERCEL_URL",
    "VERCEL_PROJECT_PRODUCTION_URL",
]:
    val = os.getenv(var)
    # Normalize Vercel-provided hostnames to full https URL if needed
    if val and not val.startswith("http"):
        val = f"https://{val}"
    if val and val not in origins:
        origins.append(val)

print(f"[startup] CORS allow_origins resolved: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Allow Vercel preview deployments like https://<branch>-<hash>-<project>.vercel.app
    allow_origin_regex=r"^https://[a-z0-9-]+\.vercel\.app$",
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Email Generator API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
        "health": "/health",
        "endpoints": {
            "email": "/api/v1/email",
            "auth": "/api/auth",
            "users": "/api/v1/users"
        }
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Lightweight readiness endpoint for monitoring."""
    return HealthCheckResponse(
        status="ok",
        app_name=settings.app_name,
        version="1.0.0"
    )


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(email.router, prefix="/api/v1/email", tags=["email"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])
 


# Entrypoint hint for `uvicorn src.api.main:app --reload`
__all__ = ["app"]
