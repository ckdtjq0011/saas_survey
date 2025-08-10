from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional, List
from functools import lru_cache
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields in .env
    )
    
    # Application
    PROJECT_NAME: str = "SaaS Survey"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./survey.db"
    
    # Security - REQUIRED from environment
    SECRET_KEY: str = Field(..., min_length=32)  # Required field with minimum length
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"])
    
    # Email Configuration (Optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: Optional[str] = None
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = Field(default=[".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png"])
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from environment variable"""
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            try:
                return json.loads(self.BACKEND_CORS_ORIGINS)
            except json.JSONDecodeError:
                return self.BACKEND_CORS_ORIGINS.split(",")
        return self.BACKEND_CORS_ORIGINS


@lru_cache()
def get_settings() -> Settings:
    """
    Create and cache settings instance.
    Use this function to get settings throughout the application.
    """
    return Settings()


# For backward compatibility
settings = get_settings()