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

# Configure CORS - Railway-compatible
origins = list(settings.cors_origins) if settings.cors_origins else [
    "http://localhost:5173",
    "http://localhost:3000",
]

# Add Railway frontend URL if deployed
railway_frontend_url = os.getenv("RAILWAY_FRONTEND_URL")
if railway_frontend_url and railway_frontend_url not in origins:
    origins.append(railway_frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
            "auth": "/api/v1/auth",
            "users": "/api/v1/users"
        }
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Lightweight readiness endpoint for monitoring."""
    return HealthCheckResponse(app_name=settings.app_name)


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(email.router, prefix="/api/v1/email", tags=["email"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])


# Entrypoint hint for `uvicorn src.api.main:app --reload`
__all__ = ["app"]
