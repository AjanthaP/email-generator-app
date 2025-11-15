#!/usr/bin/env python3
"""Railway deployment readiness checklist (diagnostics).

Run before deploying to confirm required files & env variables.
Usage:
    python scripts/diagnostics/check_railway.py
"""
import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} missing: {filepath}")
        return False

def check_env_var(var_name, required=True):
    value = os.getenv(var_name)
    if value:
        if any(key in var_name.upper() for key in ['KEY', 'SECRET', 'PASSWORD']):
            display = value[:10] + "..." if len(value) > 10 else "***"
        else:
            display = value
        print(f"✅ {var_name} = {display}")
        return True
    else:
        if required:
            print(f"❌ {var_name} not set (required)")
        else:
            print(f"⚠️  {var_name} not set (optional)")
        return not required

def main():
    print("=" * 60)
    print("Railway Deployment Readiness Check")
    print("=" * 60)    
    all_passed = True
    print("\n📁 Checking required files...")
    all_passed &= check_file_exists("Dockerfile", "Dockerfile")
    all_passed &= check_file_exists("railway.json", "Railway config")
    all_passed &= check_file_exists(".dockerignore", "Docker ignore")
    all_passed &= check_file_exists("requirements.txt", "Requirements")
    all_passed &= check_file_exists("src/api/main.py", "FastAPI app")

    print("\n🔐 Checking environment variables...")
    env_file = Path(".env")
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
    all_passed &= check_env_var("GEMINI_API_KEY", required=True)
    all_passed &= check_env_var("JWT_SECRET_KEY", required=True)
    check_env_var("GOOGLE_CLIENT_ID", required=False)
    check_env_var("GOOGLE_CLIENT_SECRET", required=False)
    check_env_var("ENABLE_GOOGLE_OAUTH", required=False)
    check_env_var("REDIS_URL", required=False)
    check_env_var("MONGODB_CONNECTION_STRING", required=False)

    print("\n🐍 Checking Python version...")
    py_version = sys.version_info
    if py_version.major == 3 and py_version.minor >= 10:
        print(f"✅ Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        print(f"❌ Python {py_version.major}.{py_version.minor} - Need Python 3.10+")
        all_passed = False

    print("\n📦 Checking core dependencies...")
    try:
        import fastapi  # noqa: F401
        print("✅ FastAPI installed")
    except ImportError:
        print("❌ FastAPI not installed")
        all_passed = False
    try:
        import uvicorn  # noqa: F401
        print("✅ Uvicorn installed")
    except ImportError:
        print("❌ Uvicorn not installed")
        all_passed = False

    print("\n=" * 60)
    if all_passed:
        print("✅ ALL CHECKS PASSED - Ready to deploy!")
    else:
        print("❌ SOME CHECKS FAILED - Fix issues before deploying")
    print("=" * 60)
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
