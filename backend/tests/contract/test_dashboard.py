import json
import uuid
from collections.abc import Callable, Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fraud_api.api.dependencies import get_model_provider
from fraud_api.db.models import ModelVersionRecord
from fraud_api.db.seed import seed_reference_data
from fraud_api.db.session import get_session
from fraud_api.main import create_app
from fraud_api.models.loader import ModelBundle
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session


@pytest.fixture
def dashboard_client(
    engine: Engine, model_provider: Callable[[], ModelBundle]
) -> Generator[tuple[TestClient, Engine], None, None]:
    with Session(engine) as seed_session:
        seed_reference_data(seed_session)
        seed_session.commit()
    app = create_app()

    def session_override() -> Generator[Session, None, None]:
        with Session(engine, expire_on_commit=False) as session:
            yield session
            session.commit()

    app.dependency_overrides[get_session] = session_override
    app.dependency_overrides[get_model_provider] = lambda: model_provider
    with TestClient(app) as client:
        yield client, engine


def test_dashboard_range_and_active_model_contract(dashboard_client) -> None:
    client, engine = dashboard_client
    now = datetime.now(UTC)
    payload = json.loads(Path("tests/fixtures/transaction.json").read_text())
    payload["id"] = str(uuid.uuid4())
    payload["eventTime"] = now.isoformat()
    assert client.post("/api/v1/transactions", json=payload).status_code == 201
    with Session(engine) as session:
        model = session.scalar(select(ModelVersionRecord))
        assert model is not None
        model.metrics = {
            "precision": 0.8,
            "recall": 0.7,
            "pr_auc": 0.75,
            "true_positive": 7,
            "false_positive": 2,
            "true_negative": 90,
            "false_negative": 3,
            "alert_volume": 9,
        }
        session.commit()

    summary = client.get(
        "/api/v1/dashboard/summary",
        params={
            "start": (now - timedelta(days=1)).isoformat(),
            "end": (now + timedelta(days=1)).isoformat(),
        },
    )
    model = client.get("/api/v1/models/active")

    assert summary.status_code == model.status_code == 200
    assert summary.json()["totals"] == {
        "transactions": 1,
        "alerts": 1,
        "amountAtRisk": "800.00",
    }
    assert model.json()["metrics"]["prAuc"] == 0.75
    assert model.json()["datasetId"] == "fixture-dataset"


def test_dashboard_rejects_reversed_range(dashboard_client) -> None:
    client, _ = dashboard_client
    now = datetime.now(UTC)
    response = client.get(
        "/api/v1/dashboard/summary",
        params={"start": now.isoformat(), "end": (now - timedelta(days=1)).isoformat()},
    )
    assert response.status_code == 422
