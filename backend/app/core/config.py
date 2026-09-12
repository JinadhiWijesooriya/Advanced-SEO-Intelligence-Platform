import os
from typing import List
from pydantic import validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Advanced SEO Intelligence Platform"
    VERSION: str = "1.1.0"
    API_V1_STR: str = "/api/v1"

    # SQLite initially as specified in Phase 1 roadmap
    DATABASE_URL: str = "sqlite:///./seo_platform.db"

    SECRET_KEY: str = "dev-secret-key-change-in-production-1234567890"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Celery & Redis configuration (Phase 7)
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    USE_CELERY: bool = False

    # Phase 10: AI Intelligence
    OPENAI_API_KEY: str = ""
    AI_ENABLED: bool = True

    # Phase 10: Structured Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"   # "text" for dev, "json" for production

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

