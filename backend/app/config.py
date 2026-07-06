"""
PredictV Application Configuration.

Loads settings from environment variables with sensible defaults.
"""

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "PredictV"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./predictv.db"

    @property
    def sync_database_url(self) -> str:
        return self.DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "")

    # Security
    SECRET_KEY: str = "change-me-to-a-random-64-char-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ML Models
    MODEL_DIR: str = "./ml_models"
    SYNTHETIC_DATA_DIR: str = "./data"

    # Reports
    REPORT_DIR: str = "./reports"

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@predictv.com"

    @property
    def model_path(self) -> Path:
        path = Path(self.MODEL_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def report_path(self) -> Path:
        path = Path(self.REPORT_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def data_path(self) -> Path:
        path = Path(self.SYNTHETIC_DATA_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
