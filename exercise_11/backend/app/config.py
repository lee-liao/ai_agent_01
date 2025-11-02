"""
Configuration settings for the Child Growth Assistant backend.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI API - Optional for testing, required for production
    OPENAI_API_KEY: Optional[str] = None
    
    # Optional settings with defaults
    CORS_ORIGINS: str = "http://localhost:3082,http://localhost:3000"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Global settings instance
try:
    settings = Settings()
except Exception:
    # Fallback if .env doesn't exist
    settings = Settings(
        OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
        CORS_ORIGINS="http://localhost:3082,http://localhost:3000"
    )

