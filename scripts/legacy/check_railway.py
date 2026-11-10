#!/usr/bin/env python3
"""
Quick deployment checker for Railway readiness
Run this before deploying to catch common issues
"""

import os
import sys
from pathlib import Path


def check_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} missing: {filepath}")
        return False


def check_env_var(var_name, required=True):
    """Check if environment variable is set."""
    value = os.getenv(var_name)
    if value:
        # Mask sensitive values
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
    """Run all checks."""
    print("=" * 60)
    print("Railway Deployment Readiness Check")
    print("=" * 60)
    print()
    
    all_passed = True
    
    # Check files
    print("📁 Checking required files...")
    all_passed &= check_file_exists("Dockerfile", "Dockerfile")
    all_passed &= check_file_exists("railway.json", "Railway config")
    all_passed &= check_file_exists(".dockerignore", "Docker ignore")
    all_passed &= check_file_exists("requirements.txt", "Requirements")
    all_passed &= check_file_exists("src/api/main.py", "FastAPI app")
    print()
    
    # Check environment (from .env file if exists)
    print("🔐 Checking environment variables...")
    
    # Load .env if exists
    env_file = Path(".env")
    if env_file.exists():
        print("Loading .env file for local check...")
        from dotenv import load_dotenv
        load_dotenv()
    
    # Required variables
    all_passed &= check_env_var("GEMINI_API_KEY", required=True)
    all_passed &= check_env_var("JWT_SECRET_KEY", required=True)
    
    # OAuth variables
    check_env_var("GOOGLE_CLIENT_ID", required=False)
    check_env_var("GOOGLE_CLIENT_SECRET", required=False)
    check_env_var("ENABLE_GOOGLE_OAUTH", required=False)
    
    # Optional services
    check_env_var("REDIS_URL", required=False)
    check_env_var("MONGODB_CONNECTION_STRING", required=False)
    
    print()
    
    # Check Python version
    print("🐍 Checking Python version...")
    py_version = sys.version_info
    if py_version.major == 3 and py_version.minor >= 10:
        print(f"✅ Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        print(f"❌ Python {py_version.major}.{py_version.minor} - Need Python 3.10+")
        all_passed = False
    print()
    
    # Check dependencies
    print("📦 Checking dependencies...")
    try:
        import fastapi
        print(f"✅ FastAPI {fastapi.__version__}")
    except ImportError:
        print("❌ FastAPI not installed")
        all_passed = False
    
    try:
        import uvicorn
        print(f"✅ Uvicorn installed")
    except ImportError:
        print("❌ Uvicorn not installed")
        all_passed = False
    
    try:
        import langchain
        print(f"✅ LangChain installed")
    except ImportError:
        print("⚠️  LangChain not installed (run: pip install -r requirements.txt)")
    
    print()
    
    # Final verdict
    print("=" * 60)
    if all_passed:
        print("✅ ALL CHECKS PASSED - Ready to deploy!")
        print()
        print("Next steps:")
        print("1. Push to GitHub: git push origin main")
        print("2. Connect Railway to your repo")
        print("3. Add environment variables in Railway dashboard")
        print("4. Railway will auto-deploy")
        print()
        print("📖 See RAILWAY_DEPLOYMENT.md for detailed instructions")
    else:
        print("❌ SOME CHECKS FAILED - Fix issues before deploying")
        print()
        print("Common fixes:")
        print("- Set GEMINI_API_KEY in .env or Railway dashboard")
        print("- Generate JWT_SECRET_KEY: python -c 'import secrets; print(secrets.token_urlsafe(32))'")
        print("- Run: pip install -r requirements.txt")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
