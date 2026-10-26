"""
Server Configuration
Loaded from server/.env via Pydantic BaseSettings.
"""

from pathlib import Path
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

PLACEHOLDER_SECRETS = {
    "placeholder",
    "changeme",
    "your-secret-key",
    "secret",
    "change_me_super_secret",
    "replace_with_secure_random_key",
    "your_jwt_secret_key_here",
    "replace_with_secure_jwt_secret",
}

PLACEHOLDER_PASSWORDS = {
    "placeholder",
    "changeme",
    "admin123",
    "password",
    "replace_with_secure_password",
    "admin_password_here",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 1440
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:5173,http://127.0.0.1:5173"
    WS_PUSH_INTERVAL_SECONDS: float = 1.0

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        clean = v.strip().lower()
        if (
            not v
            or "<your_" in clean
            or "placeholder" in clean
            or "changeme" in clean
            or "replace_with" in clean
        ):
            raise ValueError(
                "Refusing to start: DATABASE_URL contains placeholder values. "
                "Please configure a valid database connection string in server/.env."
            )
        return v

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        clean = v.strip().lower()
        if (
            not v
            or clean in PLACEHOLDER_SECRETS
            or "placeholder" in clean
            or "replace_with" in clean
            or len(v) < 16
        ):
            raise ValueError(
                "Refusing to start: JWT_SECRET is set to an insecure default or placeholder value. "
                "Please configure a strong random secret (min 16 chars) in server/.env."
            )
        return v

    @field_validator("ADMIN_PASSWORD")
    @classmethod
    def validate_admin_password(cls, v: str) -> str:
        clean = v.strip().lower()
        if (
            not v
            or clean in PLACEHOLDER_PASSWORDS
            or "placeholder" in clean
            or "replace_with" in clean
            or len(v) < 8
        ):
            raise ValueError(
                "Refusing to start: ADMIN_PASSWORD is set to a default placeholder. "
                "Please set a strong password (min 8 chars) in server/.env."
            )
        return v

    @property
    def cors_origin_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
