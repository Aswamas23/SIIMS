from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://siims_user:siims_pass@localhost:5432/siims_db"

    # Security
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"

    # Admin seeding
    ADMIN_EMAIL: str = "admin@school.edu"
    ADMIN_PASSWORD: str = "Admin@123456"

    # SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "SIIMS <noreply@school.edu>"

    # Fernet key for encrypting SMTP password at rest
    FERNET_KEY: str = ""

    # App metadata
    APP_TITLE: str = "SIIMS API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    @computed_field
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Ensure asyncpg dialect is used."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()
