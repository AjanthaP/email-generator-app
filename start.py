"""
Railway-compatible startup script
Handles environment detection and service initialization
"""
import os
import sys
import uvicorn


def main():
    """Start the FastAPI application with Railway-compatible settings."""
    # Railway sets PORT env var
    port = int(os.getenv("PORT", 8000))
    
    # Detect environment
    is_production = os.getenv("RAILWAY_ENVIRONMENT") == "production"
    is_railway = os.getenv("RAILWAY_ENVIRONMENT") is not None
    
    # Configure based on environment
    config = {
        "app": "src.api.main:app",
        "host": "0.0.0.0",
        "port": port,
    }
    
    if is_production or is_railway:
        # Production settings
        workers = int(os.getenv("WEB_CONCURRENCY", 4))
        config.update({
            "workers": workers,
            "log_level": "warning",
            "access_log": True,
            "proxy_headers": True,
            "forwarded_allow_ips": "*",
        })
        print(f"🚀 Starting in PRODUCTION mode on port {port} with {workers} workers")
    else:
        # Development settings
        config.update({
            "reload": True,
            "log_level": "info",
        })
        print(f"🔧 Starting in DEVELOPMENT mode on port {port}")
    
    uvicorn.run(**config)


if __name__ == "__main__":
    main()
