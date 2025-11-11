from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash-exp"
    
    # Application Settings
    app_name: str = "AI Email Assistant"
    debug: bool = False
    log_level: str = "INFO"
    
    # LLM Settings
    max_tokens: int = 1000
    temperature: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
