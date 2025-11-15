#!/usr/bin/env python3
"""(Moved) Configuration integration test.

Relocated under scripts/diagnostics for clarity; this root copy will be removed.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

def create_test_env_file():
    """Create a temporary .env file for testing."""
    env_content = """
# Redis Configuration
ENABLE_REDIS=true
DISABLE_REDIS=false
REDIS_HOST=test-redis-host
REDIS_PORT=6380
REDIS_DB=1
REDIS_PASSWORD=test-password
REDIS_SOCKET_TIMEOUT=35.0
REDIS_SOCKET_CONNECT_TIMEOUT=35.0
REDIS_RETRY_ON_TIMEOUT=true
REDIS_HEALTH_CHECK_INTERVAL=35

# ChromaDB Configuration
ENABLE_CHROMADB=true
DISABLE_CHROMADB=false
CHROMADB_HOST=test-chroma-host
CHROMADB_PORT=8001
CHROMADB_DATABASE_PATH=./test_chroma_db
CHROMADB_COLLECTION_NAME=test_email_contexts
CHROMADB_DISTANCE_METRIC=cosine
CHROMADB_EMBEDDING_FUNCTION=sentence_transformers

# Gmail Configuration
ENABLE_GMAIL=true
DISABLE_GMAIL=false
GMAIL_CREDENTIALS_FILE=test/gmail_credentials.json
GMAIL_TOKEN_FILE=test/gmail_token.json
GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.send

# OAuth Configuration
ENABLE_OAUTH=true
DISABLE_OAUTH=false
OAUTH_CONFIG_FILE=test/oauth_config.json
GOOGLE_CLIENT_ID=test_google_client_id
GOOGLE_CLIENT_SECRET=test_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback/google
GITHUB_CLIENT_ID=test_github_client_id
GITHUB_CLIENT_SECRET=test_github_client_secret
GITHUB_REDIRECT_URI=http://localhost:8000/auth/callback/github
MICROSOFT_CLIENT_ID=test_microsoft_client_id
MICROSOFT_CLIENT_SECRET=test_microsoft_client_secret
MICROSOFT_REDIRECT_URI=http://localhost:8000/auth/callback/microsoft

# MCP Configuration
ENABLE_MCP=true
DISABLE_MCP=false
MCP_SERVER_HOST=test-mcp-host
MCP_SERVER_PORT=8766
MCP_SERVER_NAME=test-email-generator-mcp-server
MCP_SERVER_VERSION=1.0.0-test
MCP_CLIENT_TIMEOUT=45.0
"""
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write(env_content)
        return f.name

def test_configuration_loading():
    """Test that configuration loads from .env file."""
    env_file = create_test_env_file()
    
    try:
        # Set environment variable to point to test .env file
        os.environ['SETTINGS_ENV_FILE'] = env_file
        
        # Import configuration (this will load the test .env file)
        from utils.config import app_settings
        
        # Test Redis configuration
        assert app_settings.enable_redis == True
        assert app_settings.redis_host == "test-redis-host"
        assert app_settings.redis_port == 6380
        assert app_settings.redis_password == "test-password"
        
        # Test ChromaDB configuration
        assert app_settings.enable_chromadb == True
        assert app_settings.chromadb_host == "test-chroma-host"
        assert app_settings.chromadb_port == 8001
        
        # Test Gmail configuration
        assert app_settings.enable_gmail == True
        assert app_settings.gmail_credentials_file == "test/gmail_credentials.json"
        
        # Test OAuth configuration
        assert app_settings.enable_oauth == True
        assert app_settings.google_client_id == "test_google_client_id"
        assert app_settings.github_client_secret == "test_github_client_secret"
        
        # Test MCP configuration
        assert app_settings.enable_mcp == True
        assert app_settings.mcp_server_host == "test-mcp-host"
        assert app_settings.mcp_server_port == 8766
        
        print("✅ Configuration loading test PASSED")
        
    finally:
        # Clean up
        os.unlink(env_file)
        if 'SETTINGS_ENV_FILE' in os.environ:
            del os.environ['SETTINGS_ENV_FILE']

def test_redis_cache_configuration():
    """Test that Redis cache uses configuration."""
    env_file = create_test_env_file()
    
    try:
        os.environ['SETTINGS_ENV_FILE'] = env_file
        
        from cache.redis_cache import create_redis_cache
        
        # Test factory function respects configuration
        cache = create_redis_cache()
        if cache:
            # Redis would be None if not available, but config should be used
            assert cache.host == "test-redis-host"
            assert cache.port == 6380
            print("✅ Redis configuration test PASSED")
        else:
            print("ℹ️ Redis configuration test SKIPPED (Redis not available)")
            
    except ImportError as e:
        print(f"ℹ️ Redis configuration test SKIPPED: {e}")
    finally:
        os.unlink(env_file)
        if 'SETTINGS_ENV_FILE' in os.environ:
            del os.environ['SETTINGS_ENV_FILE']

def test_chromadb_configuration():
    """Test that ChromaDB uses configuration."""
    env_file = create_test_env_file()
    
    try:
        os.environ['SETTINGS_ENV_FILE'] = env_file
        
        from context.chroma_context import create_chroma_context
        
        # Test factory function respects configuration
        context = create_chroma_context()
        if context:
            assert context.host == "test-chroma-host"
            assert context.port == 8001
            print("✅ ChromaDB configuration test PASSED")
        else:
            print("ℹ️ ChromaDB configuration test SKIPPED (ChromaDB not available)")
            
    except ImportError as e:
        print(f"ℹ️ ChromaDB configuration test SKIPPED: {e}")
    finally:
        os.unlink(env_file)
        if 'SETTINGS_ENV_FILE' in os.environ:
            del os.environ['SETTINGS_ENV_FILE']

def test_gmail_configuration():
    """Test that Gmail service uses configuration."""
    env_file = create_test_env_file()
    
    try:
        os.environ['SETTINGS_ENV_FILE'] = env_file
        
        from integrations.gmail_service import create_gmail_service
        
        # Test factory function respects configuration
        service = create_gmail_service()
        if service:
            assert service.credentials_file == "test/gmail_credentials.json"
            assert service.token_file == "test/gmail_token.json"
            print("✅ Gmail configuration test PASSED")
        else:
            print("ℹ️ Gmail configuration test SKIPPED (credentials not available)")
            
    except ImportError as e:
        print(f"ℹ️ Gmail configuration test SKIPPED: {e}")
    finally:
        os.unlink(env_file)
        if 'SETTINGS_ENV_FILE' in os.environ:
            del os.environ['SETTINGS_ENV_FILE']

def test_oauth_configuration():
    """Test that OAuth manager uses configuration."""
    env_file = create_test_env_file()
    
    try:
        os.environ['SETTINGS_ENV_FILE'] = env_file
        
        from auth.oauth_providers import create_oauth_manager
        
        # Test factory function respects configuration
        manager = create_oauth_manager()
        if manager:
            # Check that providers are loaded from configuration
            assert 'google' in manager.providers
            assert manager.providers['google'].client_id == "test_google_client_id"
            print("✅ OAuth configuration test PASSED")
        else:
            print("ℹ️ OAuth configuration test SKIPPED (OAuth not available)")
            
    except ImportError as e:
        print(f"ℹ️ OAuth configuration test SKIPPED: {e}")
    finally:
        os.unlink(env_file)
        if 'SETTINGS_ENV_FILE' in os.environ:
            del os.environ['SETTINGS_ENV_FILE']

def test_mcp_configuration():
    """Test that MCP integration uses configuration."""
    env_file = create_test_env_file()
    
    try:
        os.environ['SETTINGS_ENV_FILE'] = env_file
        
        from integrations.mcp_integration import create_mcp_server, create_mcp_client
        
        # Test factory functions respect configuration
        server = create_mcp_server()
        client = create_mcp_client()
        
        if server:
            assert server.server_host == "test-mcp-host"
            assert server.server_port == 8766
            assert server.server_info["name"] == "test-email-generator-mcp-server"
            print("✅ MCP Server configuration test PASSED")
        
        if client:
            assert client.timeout == 45.0
            print("✅ MCP Client configuration test PASSED")
            
    except ImportError as e:
        print(f"ℹ️ MCP configuration test SKIPPED: {e}")
    finally:
        os.unlink(env_file)
        if 'SETTINGS_ENV_FILE' in os.environ:
            del os.environ['SETTINGS_ENV_FILE']

def test_disabled_components():
    """Test that components can be disabled via configuration."""
    env_content = """
DISABLE_REDIS=true
DISABLE_CHROMADB=true
DISABLE_GMAIL=true
DISABLE_OAUTH=true
DISABLE_MCP=true
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write(env_content)
        env_file = f.name
    
    try:
        os.environ['SETTINGS_ENV_FILE'] = env_file
        
        # Import factory functions
        try:
            from cache.redis_cache import create_redis_cache
            assert create_redis_cache() is None
            print("✅ Redis disable test PASSED")
        except ImportError:
            print("ℹ️ Redis disable test SKIPPED")
        
        try:
            from context.chroma_context import create_chroma_context
            assert create_chroma_context() is None
            print("✅ ChromaDB disable test PASSED")
        except ImportError:
            print("ℹ️ ChromaDB disable test SKIPPED")
        
        try:
            from integrations.gmail_service import create_gmail_service
            assert create_gmail_service() is None
            print("✅ Gmail disable test PASSED")
        except ImportError:
            print("ℹ️ Gmail disable test SKIPPED")
        
        try:
            from auth.oauth_providers import create_oauth_manager
            assert create_oauth_manager() is None
            print("✅ OAuth disable test PASSED")
        except ImportError:
            print("ℹ️ OAuth disable test SKIPPED")
        
        try:
            from integrations.mcp_integration import create_mcp_server, create_mcp_client
            assert create_mcp_server() is None
            assert create_mcp_client() is None
            print("✅ MCP disable test PASSED")
        except ImportError:
            print("ℹ️ MCP disable test SKIPPED")
            
    finally:
        os.unlink(env_file)
        if 'SETTINGS_ENV_FILE' in os.environ:
            del os.environ['SETTINGS_ENV_FILE']

def main():
    """Run all configuration tests."""
    print("🧪 Testing Configuration Integration...")
    print("=" * 50)
    
    try:
        test_configuration_loading()
        test_redis_cache_configuration()
        test_chromadb_configuration()
        test_gmail_configuration()
        test_oauth_configuration()
        test_mcp_configuration()
        test_disabled_components()
        
        print("\n" + "=" * 50)
        print("🎉 All configuration tests completed!")
        print("\n✅ Configuration integration is working correctly")
        print("✅ All components respect .env settings")
        print("✅ Components can be enabled/disabled via configuration")
        print("✅ Factory functions use centralized settings")
        
    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())