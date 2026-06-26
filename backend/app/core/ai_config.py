"""
Nura - AI Settings
Pydantic settings for AI Core Infrastructure
"""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.core.exceptions import AIConfigurationError


class AISettings(BaseSettings):
    """AI application settings loaded from environment variables"""
    
    GROQ_API_KEY: str = Field(default="", description="API key for Groq service authentication")
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile", description="Model name to use for Groq service")
    
    # Exposed Model Names
    MODEL_LLAMA_3_3_70B: str = "llama-3.3-70b-versatile"
    MODEL_LLAMA_3_1_8B: str = "llama-3.1-8b-instant"
    MODEL_MIXTRAL_8X7B: str = "mixtral-8x7b-32768"
    
    # Request configuration
    TIMEOUT_SECONDS: float = Field(default=30.0, description="Request timeout for Groq API in seconds")
    
    # Retry configuration
    MAX_RETRIES: int = Field(default=3, description="Maximum number of retries for Groq API calls")
    RETRY_MIN_DELAY: float = Field(default=1.0, description="Minimum delay between retries in seconds")
    RETRY_MAX_DELAY: float = Field(default=10.0, description="Maximum delay between retries in seconds")
    
    # Token limits
    TOKEN_LIMIT_LLAMA_3_3_70B: int = 128000
    TOKEN_LIMIT_LLAMA_3_1_8B: int = 131072
    TOKEN_LIMIT_MIXTRAL_8X7B: int = 32768

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("GROQ_MODEL", mode="before")
    @classmethod
    def clean_model_name(cls, v: Optional[str]) -> str:
        """Handle possible duplicate key assignment format e.g. GROQ_MODEL=GROQ_MODEL=model-name"""
        if not v:
            return "llama-3.3-70b-versatile"
        if isinstance(v, str) and "GROQ_MODEL=" in v:
            return v.replace("GROQ_MODEL=", "").strip()
        return v

    def validate_config(self) -> None:
        """Manually validate config values and throw custom exceptions"""
        if not self.GROQ_API_KEY or self.GROQ_API_KEY.strip() == "":
            raise AIConfigurationError("GROQ_API_KEY environment variable is required and cannot be empty")


# Singleton instance
ai_settings = AISettings()
