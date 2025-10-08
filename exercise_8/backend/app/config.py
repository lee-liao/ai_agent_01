"""
Configuration settings for Exercise 8 HITL Contract Redlining Orchestrator
Handles environment variables and application settings
"""

import os
import json
from typing import List, Optional, Any, Dict
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # =============================================================================
    # APPLICATION SETTINGS
    # =============================================================================
    app_name: str = Field(default="HITL Contract Redlining Orchestrator", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # =============================================================================
    # DATABASE SETTINGS
    # =============================================================================
    database_url: str = Field(
        default="postgresql+asyncpg://exercise8:exercise8password@localhost:5432/exercise8",
        env="DATABASE_URL"
    )
    db_pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    # =============================================================================
    # REDIS SETTINGS
    # =============================================================================
    redis_url: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL"
    )
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    enable_query_cache: bool = Field(default=True, env="ENABLE_QUERY_CACHE")
    enable_embedding_cache: bool = Field(default=True, env="ENABLE_EMBEDDING_CACHE")
    
    # =============================================================================
    # LLM API SETTINGS
    # =============================================================================
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-3-small", env="OPENAI_EMBEDDING_MODEL")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-sonnet-20240229", env="ANTHROPIC_MODEL")
    
    # =============================================================================
    # EMBEDDING SETTINGS
    # =============================================================================
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=384, env="EMBEDDING_DIMENSION")
    embedding_batch_size: int = Field(default=32, env="EMBEDDING_BATCH_SIZE")
    use_openai_embeddings: bool = Field(default=False, env="USE_OPENAI_EMBEDDINGS")
    
    # =============================================================================
    # FILE UPLOAD SETTINGS
    # =============================================================================
    max_file_size: str = Field(default="50MB", env="MAX_FILE_SIZE")
    allowed_file_types: str = Field(
        default="pdf,txt,docx,md",
        env="ALLOWED_FILE_TYPES"
    )
    upload_directory: str = Field(default="./uploads", env="UPLOAD_DIRECTORY")
    temp_directory: str = Field(default="./temp", env="TEMP_DIRECTORY")
    
    # =============================================================================
    # CONTRACT ANALYSIS SETTINGS
    # =============================================================================
    clause_chunk_size: int = Field(default=500, env="CLAUSE_CHUNK_SIZE")
    clause_overlap: int = Field(default=50, env="CLAUSE_OVERLAP")
    
    max_retrieved_clauses: int = Field(default=10, env="MAX_RETRIEVED_CLAUSES")
    similarity_threshold: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    
    max_response_length: int = Field(default=2000, env="MAX_RESPONSE_LENGTH")
    temperature: float = Field(default=0.7, env="TEMPERATURE")
    top_p: float = Field(default=0.9, env="TOP_P")
    
    # =============================================================================
    # SECURITY SETTINGS
    # =============================================================================
    secret_key: str = Field(
        default="your_secret_key_here_change_in_production",
        env="SECRET_KEY"
    )
    jwt_secret_key: str = Field(
        default="your_jwt_secret_key_here",
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    # =============================================================================
    # CORS SETTINGS
    # =============================================================================
    cors_origins: str = Field(
        default="*",  # Allow all origins for student class
        env="CORS_ORIGINS"
    )
    
    # =============================================================================
    # PERFORMANCE SETTINGS
    # =============================================================================
    max_concurrent_requests: int = Field(default=100, env="MAX_CONCURRENT_REQUESTS")
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    
    # =============================================================================
    # AGENT CONTROL SETTINGS (Exercise 8)
    # =============================================================================
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")

    # Failure injection knobs
    fail_rate: float = Field(default=0.35, env="FAIL_RATE")
    inject_timeout_ms: int = Field(default=800, env="INJECT_TIMEOUT_MS")
    cache_hit_rate: float = Field(default=0.7, env="CACHE_HIT_RATE")

    # Budget & model
    budget_usd: float = Field(default=0.05, env="BUDGET_USD")
    model: str = Field(default="gpt-4o-mini", env="MODEL")

    # Retry & circuit breaker
    max_retries: int = Field(default=2, env="MAX_RETRIES")
    circuit_failures_threshold: int = Field(default=3, env="CIRCUIT_FAILURES_THRESHOLD")
    circuit_window_seconds: int = Field(default=60, env="CIRCUIT_WINDOW_SECONDS")
    circuit_cooldown_seconds: int = Field(default=60, env="CIRCUIT_COOLDOWN_SECONDS")

    # Prompt AB
    prompt_ab_v2_percent: float = Field(default=0.10, env="PROMPT_AB_V2_PERCENT")

    # =============================================================================
    # OBSERVABILITY SETTINGS
    # =============================================================================
    jaeger_endpoint: Optional[str] = Field(default=None, env="JAEGER_ENDPOINT")
    otel_service_name: str = Field(default="exercise8-backend", env="OTEL_SERVICE_NAME")
    otel_service_version: str = Field(default="1.0.0", env="OTEL_SERVICE_VERSION")
    otel_console_export: bool = Field(default=True, env="OTEL_CONSOLE_EXPORT")
    
    # =============================================================================
    # VALIDATORS
    # =============================================================================
    
    @field_validator('cors_origins', mode='before')
    def parse_cors_origins(cls, v):
        # Handle None or empty values
        if v is None or (isinstance(v, str) and not v.strip()):
            return "*"
        if isinstance(v, str):
            return v  # Return the string as-is
        return v
    
    @field_validator('allowed_file_types', mode='before')
    def parse_allowed_file_types(cls, v):
        # Handle None or empty values
        if v is None or (isinstance(v, str) and not v.strip()):
            return ""
        if isinstance(v, str):
            return v  # Return the string as-is
        return v
    
    @field_validator('max_file_size')
    def parse_max_file_size(cls, v):
        """Convert file size string to bytes"""
        if isinstance(v, str):
            v = v.upper()
            if v.endswith('MB'):
                return int(float(v[:-2]) * 1024 * 1024)
            elif v.endswith('KB'):
                return int(float(v[:-2]) * 1024)
            elif v.endswith('GB'):
                return int(float(v[:-2]) * 1024 * 1024 * 1024)
            else:
                return int(v)
        return v
    
    @field_validator('environment')
    def validate_environment(cls, v):
        allowed_envs = ['development', 'testing', 'staging', 'production']
        if v not in allowed_envs:
            raise ValueError(f'Environment must be one of: {allowed_envs}')
        return v
    
    @field_validator('log_level')
    def validate_log_level(cls, v):
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Log level must be one of: {allowed_levels}')
        return v.upper()
    
    # =============================================================================
    # COMPUTED PROPERTIES
    # =============================================================================
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == "development"
    
    @property
    def max_file_size_mb(self) -> float:
        """Get max file size in MB"""
        return self.max_file_size / (1024 * 1024)
    
    @property
    def contract_analysis_model(self) -> str:
        """Get the model to use for contract analysis"""
        return self.openai_model

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration dictionary"""
        return {
            "url": self.database_url,
            "pool_size": self.db_pool_size,
            "max_overflow": self.db_max_overflow,
            "pool_timeout": self.db_pool_timeout,
        }
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration dictionary"""
        return {
            "openai": {
                "api_key": self.openai_api_key,
                "model": self.openai_model,
                "embedding_model": self.openai_embedding_model,
            },
            "anthropic": {
                "api_key": self.anthropic_api_key,
                "model": self.anthropic_model,
            },
            "generation": {
                "max_response_length": self.max_response_length,
                "temperature": self.temperature,
                "top_p": self.top_p,
            }
        }
    
    def get_contract_analysis_config(self) -> Dict[str, Any]:
        """Get contract analysis configuration dictionary"""
        return {
            "chunking": {
                "clause_chunk_size": self.clause_chunk_size,
                "clause_overlap": self.clause_overlap,
            },
            "retrieval": {
                "max_retrieved_clauses": self.max_retrieved_clauses,
                "similarity_threshold": self.similarity_threshold,
            },
            "embedding": {
                "model": self.embedding_model,
                "dimension": self.embedding_dimension,
                "batch_size": self.embedding_batch_size,
                "use_openai": self.use_openai_embeddings,
            }
        }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()