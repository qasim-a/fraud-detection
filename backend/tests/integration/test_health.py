from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fraud_api.core.config import Settings, get_settings
from fraud_api.db.session import get_session
from fraud_api.main import create_app
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

pytestmark = pytest.mark.integration


class UnavailableSession:
    def execute(self, _statement: object) -> None:
        raise OperationalError("SELECT 1", {}, Exception("offline"))


def test_health_reports_available_database_and_model(tmp_path: Path) -> None:
    artifact = tmp_path / "model.json"
    metadata = tmp_path / "metadata.json"
    artifact.write_text("{}")
    metadata.write_text("{}")
    engine = create_engine("sqlite+pysqlite:///:memory:")
    app = create_app()

    def session_override() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = session_override
    app.dependency_overrides[get_settings] = lambda: Settings(
        database_url=SecretStr("sqlite+pysqlite:///:memory:"),
        model_artifact_path=artifact,
        model_metadata_path=metadata,
    )

    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "available", "model": "available"}


def test_health_reports_degraded_dependencies(tmp_path: Path) -> None:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: UnavailableSession()
    app.dependency_overrides[get_settings] = lambda: Settings(
        database_url=SecretStr("sqlite+pysqlite:///:memory:"),
        model_artifact_path=tmp_path / "missing-model.json",
        model_metadata_path=tmp_path / "missing-metadata.json",
    )

    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "degraded",
        "database": "unavailable",
        "model": "unavailable",
    }
