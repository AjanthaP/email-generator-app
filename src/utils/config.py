from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash"
    
    # Application Settings
    app_name: str = "AI Email Assistant"
    debug: bool = False
    log_level: str = "INFO"
    
    # LLM Settings
    max_tokens: int = 1000
    temperature: float = 0.7
    
    # Stub/Test Mode
    donotusegemini: bool = False

    # Observability / Tracing (LangSmith / LangChain)
    enable_langsmith: bool = False  # master feature toggle
    langchain_tracing_v2: bool = False  # aligns with LANGCHAIN_TRACING_V2 env var
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
