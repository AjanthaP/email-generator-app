from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, List, Union
import json

class Settings(BaseSettings):
    # API Configuration
    gemini_api_key: str
    #gemini_model: str = "gemini-2.0-flash"
    gemini_model: str = "gemini-2.0-flash-lite"

    # Application Settings
    app_name: str = "AI Email Assistant"
    debug: bool = False
    log_level: str = "INFO"
    
    # LLM Settings
    max_tokens: int = 1000
    temperature: float = 0.7
    
    # Stub/Test Mode
    donotusegemini: bool = False

    # Experimental / Advanced Agent Behavior
    # When true, RouterAgent will use an LLM to decide among continue | retry | fallback
    # rather than purely deterministic rules. Falls back automatically if disabled or
    # if model invocation fails.
    enable_llm_router: bool = True

    # Observability / Tracing (LangSmith / LangChain)
    enable_langsmith: bool = False  # master feature toggle
    langchain_project: Optional[str] = None
    langsmith_api_key: Optional[str] = None  # optional override if not in LANGSMITH_API_KEY

    # Metrics / Cost Tracking
    enable_cost_tracking: bool = False
    # Pricing (USD per 1M tokens) - can be overridden via env; defaults approximate and illustrative
    price_input_per_million: float = 0.15  # hypothetical Gemini Flash input pricing
    price_output_per_million: float = 0.60  # hypothetical Gemini Flash output pricing

    # Rate Limiting (client-side guard rails)
    enable_rate_limiter: bool = False
    requests_per_minute: int = 30  # adjustable RPM limit
    tokens_per_minute: int = 60000  # adjustable TPM soft limit (estimate)
    max_concurrency: int = 4  # simple parallelism guard
    rate_limiter_jitter_ms: int = 150  # small jitter to avoid thundering herd

    # Metrics persistence
    metrics_output_dir: str = "data/metrics"
    metrics_flush_interval: int = 60  # seconds between auto flush (if implemented later)

    # === INFRASTRUCTURE CONFIGURATION ===
    
    # Redis Cache Configuration
    enable_redis: bool = True
    redis_url: str = "redis://localhost:6379"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_ssl: bool = False
    redis_decode_responses: bool = True
    redis_max_connections: int = 20
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5
    redis_retry_on_timeout: bool = True
    redis_health_check_interval: int = 30
    
    # Redis Cache TTL Settings (in seconds)
    redis_session_ttl: int = 86400  # 24 hours
    redis_profile_ttl: int = 3600   # 1 hour  
    redis_draft_ttl: int = 7200     # 2 hours
    redis_llm_response_ttl: int = 1800  # 30 minutes
    redis_rate_limit_ttl: int = 60   # 1 minute
    redis_metrics_ttl: int = 604800  # 1 week

    # PostgreSQL Database Configuration
    database_url: Optional[str] = None  # e.g., postgresql://user:pass@host:port/dbname
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_recycle: int = 3600  # Recycle connections after 1 hour
    database_echo: bool = False  # Set to True to log all SQL queries

    # ChromaDB Configuration
    enable_chromadb: bool = True
    chromadb_persist_dir: str = "data/chromadb"
    chromadb_collection_name: str = "email_contexts"
    chromadb_allow_reset: bool = False
    chromadb_anonymized_telemetry: bool = False
    chromadb_host: str = "localhost"
    chromadb_port: int = 8000
    chromadb_use_server: bool = False  # True for server mode, False for persistent local
    
    # MongoDB Configuration (alternative to local storage)
    enable_mongodb: bool = False
    mongodb_connection_string: Optional[str] = None
    mongodb_database: str = "email_generator"
    mongodb_users_collection: str = "users"
    mongodb_sessions_collection: str = "sessions"
    mongodb_profiles_collection: str = "user_profiles"
    mongodb_drafts_collection: str = "drafts"
    mongodb_contexts_collection: str = "email_contexts"
    
    # Gmail Integration Configuration
    enable_gmail: bool = True
    gmail_credentials_file: str = "config/gmail_credentials.json"
    gmail_token_file: str = "data/gmail_token.pickle"
    gmail_scopes: Union[List[str], str] = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.readonly'
    ]
    
    @field_validator('gmail_scopes', 'google_oauth_scopes', 'github_oauth_scopes', 'microsoft_oauth_scopes', mode='before')
    @classmethod
    def parse_oauth_scopes(cls, v):
        """Parse JSON string or list for OAuth scopes."""
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                return [parsed]
            except json.JSONDecodeError:
                if ',' in v:
                    return [item.strip() for item in v.split(',')]
                return [v] if v else []
        return v if isinstance(v, list) else [v]
    
    # OAuth Configuration
    enable_oauth: bool = True
    oauth_config_file: str = "config/oauth_config.json"
    
    # Google OAuth Settings
    enable_google_oauth: bool = True
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: str = "http://localhost:8501/oauth/callback"
    google_oauth_scopes: Union[List[str], str] = [
        'openid', 'email', 'profile',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    # GitHub OAuth Settings
    enable_github_oauth: bool = False
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    github_redirect_uri: str = "http://localhost:8501/oauth/github/callback"
    github_oauth_scopes: Union[List[str], str] = ['user:email', 'read:user']
    
    # Microsoft OAuth Settings
    enable_microsoft_oauth: bool = False
    microsoft_client_id: Optional[str] = None
    microsoft_client_secret: Optional[str] = None
    microsoft_redirect_uri: str = "http://localhost:8501/oauth/microsoft/callback"
    microsoft_tenant: str = "common"
    microsoft_oauth_scopes: Union[List[str], str] = [
        'openid', 'profile', 'email',
        'https://graph.microsoft.com/Mail.Send',
        'https://graph.microsoft.com/Mail.ReadWrite'
    ]
    
    # MCP (Model Context Protocol) Configuration
    enable_mcp: bool = True
    mcp_server_host: str = "localhost"
    mcp_server_port: int = 8765
    mcp_server_name: str = "email-generator-mcp-server"
    mcp_server_version: str = "1.0.0"
    mcp_server_description: str = "MCP server for AI-powered email generation"
    mcp_client_timeout: float = 30.0
    
    # Authentication Configuration
    enable_auth: bool = True
    auth_users_file: str = "data/users.json"
    auth_sessions_file: str = "data/sessions.json"
    auth_session_ttl: int = 86400  # 24 hours
    auth_max_sessions_per_user: int = 5
    auth_password_min_length: int = 8
    auth_require_email_verification: bool = False
    
    # Security Settings
    jwt_secret_key: Optional[str] = None  # Will be auto-generated if not set
    cors_origins: Union[List[str], str] = '["http://localhost:8501", "http://127.0.0.1:8501", "http://localhost:3000", "http://localhost:5173", "https://email-generator-app-frontend.vercel.app"]'
    allowed_hosts: Union[List[str], str] = '["localhost", "127.0.0.1"]'
    
    @field_validator('cors_origins', 'allowed_hosts', mode='before')
    @classmethod
    def parse_string_list(cls, v):
        """Parse JSON string or list for cors_origins and allowed_hosts."""
        if isinstance(v, str):
            try:
                # Try parsing as JSON array
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                return [parsed]  # Single string becomes list
            except json.JSONDecodeError:
                # If not JSON, split by comma or return as single item
                if ',' in v:
                    return [item.strip() for item in v.split(',')]
                return [v] if v else []
        return v if isinstance(v, list) else [v]
    
    # Feature Toggles (positive form)
    enable_redis: bool = True
    enable_chromadb: bool = True
    enable_mongodb: bool = False
    enable_gmail: bool = True
    enable_oauth: bool = True
    enable_mcp: bool = True
    enable_auth: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra env vars not defined as fields

settings = Settings()

# Derived convenience accessors (non-failing if user does not set env vars)
def pricing_for_model(model_name: str, settings: Settings = settings) -> dict:
    """Return pricing dict for a given model. Extendable for multi-model support.

    Currently a simple single-tier mapping; can be replaced by a JSON config or
    dynamic fetch later.
    """
    return {
        "model": model_name,
        "input_per_million": settings.price_input_per_million,
        "output_per_million": settings.price_output_per_million,
    }

__all__ = ["Settings", "settings", "pricing_for_model"]
