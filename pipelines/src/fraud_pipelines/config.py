"""Validated and deterministic batch-pipeline configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PipelineSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    artifact_root: Path = Path("artifacts")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    generator_seed: int = Field(default=20260727, ge=0, le=2**32 - 1)
    spark_master: str = "local[*]"
    spark_shuffle_partitions: int = Field(default=8, ge=1, le=10_000)

    @property
    def bronze_root(self) -> Path:
        return self.artifact_root / "bronze"

    @property
    def feature_root(self) -> Path:
        return self.artifact_root / "features"

    @property
    def model_root(self) -> Path:
        return self.artifact_root / "models"


@lru_cache
def get_pipeline_settings() -> PipelineSettings:
    return PipelineSettings()
