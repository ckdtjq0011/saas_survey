"""애플리케이션 설정

목적: 환경 변수를 타입 안전하게 관리
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """애플리케이션 설정 클래스

    .env 파일에서 환경 변수를 로드하고 타입 검증을 수행합니다.
    """

    # Database 설정
    storage_type: str = "sqlite"  # "csv" 또는 "sqlite"
    database_url: str = "sqlite:///./data/saas_survey.db"
    database_echo: bool = False

    secret_key: str = "development-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    redis_url: str = "redis://localhost:6379"
    redis_cache_ttl: int = 3600

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    environment: str = "development"

    data_dir: Path = Path("./data")

    session_expiry_days: int = 30

    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
