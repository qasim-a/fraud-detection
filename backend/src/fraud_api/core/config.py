"""Validated runtime configuration sourced from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with secret-safe representations."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: SecretStr = SecretStr(
        "postgresql+psycopg://fraud_app:local-development-only@localhost:5432/fraud_detection"
    )
    model_artifact_path: Path = Path("artifacts/models/active/model.json")
    model_metadata_path: Path = Path("artifacts/models/active/metadata.json")
    artifact_root: Path = Path("artifacts")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @field_validator("database_url")
    @classmethod
    def require_sqlalchemy_url(cls, value: SecretStr) -> SecretStr:
        if "://" not in value.get_secret_value():
            raise ValueError("DATABASE_URL must be a SQLAlchemy URL")
        return value

    @property
    def database_dsn(self) -> str:
        """Reveal the database URL only at the connection boundary."""
        return self.database_url.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    """Return one immutable-by-convention settings instance per process."""
    return Settings()
