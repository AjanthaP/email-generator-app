"""FastAPI backend for the AI Email Assistant.

This service exposes REST endpoints that wrap the LangGraph workflow, making it
accessible to external clients (e.g., a React front-end).
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException

from src.utils.config import settings
from .routers import auth, email, users, debug
from .schemas import HealthCheckResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the FastAPI application."""
    # Startup
    logger.info("Starting application...")
    
    # Initialize database if DATABASE_URL is configured
    if settings.database_url:
        try:
            from src.db.database import init_db
            init_db()
            logger.info("✓ Database initialized successfully")
        except Exception as e:
            logger.error(f"✗ Failed to initialize database: {e}")
            logger.warning("Application will use JSON file fallback for storage")
    else:
        logger.warning("DATABASE_URL not configured - using JSON file storage")
        logger.info("To enable PostgreSQL: Set DATABASE_URL environment variable")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    if settings.database_url:
        try:
            from src.db.database import get_db_manager
            db_manager = get_db_manager()
            db_manager.close()
            logger.info("Database connections closed")
        except Exception as e:
            logger.warning(f"Error closing database: {e}")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI-Powered Email Generation API",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
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


# Add exception handlers to ensure CORS headers on error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Ensure CORS headers are present on HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Ensure CORS headers are present on validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler to ensure CORS headers on all errors."""
    print(f"Unhandled exception: {type(exc).__name__}: {exc}")
    import traceback
    traceback.print_exc()
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        },
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
if settings.debug:
    app.include_router(debug.router, prefix="/api/debug", tags=["debug"])
 


# Entrypoint hint for `uvicorn src.api.main:app --reload`
__all__ = ["app"]
