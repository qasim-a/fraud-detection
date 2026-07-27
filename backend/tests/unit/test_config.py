from pathlib import Path

from fraud_api.core.config import Settings
from pydantic import SecretStr


def test_settings_keep_database_url_secret() -> None:
    settings = Settings(database_url=SecretStr("sqlite+pysqlite:///:memory:"))

    assert settings.database_dsn == "sqlite+pysqlite:///:memory:"
    assert "memory" not in repr(settings.database_url)


def test_model_paths_are_typed() -> None:
    settings = Settings(
        model_artifact_path=Path("model.json"), model_metadata_path=Path("meta.json")
    )

    assert settings.model_artifact_path == Path("model.json")
