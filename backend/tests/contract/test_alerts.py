import json
import uuid
from collections.abc import Callable, Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fraud_api.api.dependencies import get_model_provider
from fraud_api.db.seed import seed_reference_data
from fraud_api.db.session import get_session
from fraud_api.main import create_app
from fraud_api.models.loader import ModelBundle
from sqlalchemy import Engine
from sqlalchemy.orm import Session


@pytest.fixture
def alert_client(
    engine: Engine, model_provider: Callable[[], ModelBundle]
) -> Generator[TestClient, None, None]:
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
        yield client


def _transaction(transaction_id: uuid.UUID, event_time: datetime) -> dict[str, object]:
    payload = json.loads(Path("tests/fixtures/transaction.json").read_text())
    payload["id"] = str(transaction_id)
    payload["eventTime"] = event_time.isoformat()
    return payload


def test_alert_queue_filters_and_uses_stable_cursor(alert_client: TestClient) -> None:
    now = datetime.now(UTC)
    for offset in range(3):
        response = alert_client.post(
            "/api/v1/transactions",
            json=_transaction(uuid.uuid4(), now - timedelta(minutes=offset)),
        )
        assert response.status_code == 201

    params = {
        "start": (now - timedelta(days=1)).isoformat(),
        "end": (now + timedelta(days=1)).isoformat(),
        "status": "open",
        "minRisk": 0.9,
        "limit": 2,
    }
    first = alert_client.get("/api/v1/alerts", params=params)
    second = alert_client.get(
        "/api/v1/alerts", params={**params, "cursor": first.json()["nextCursor"]}
    )

    assert first.status_code == second.status_code == 200
    assert len(first.json()["items"]) == 2
    assert len(second.json()["items"]) == 1
    assert {item["id"] for item in first.json()["items"]}.isdisjoint(
        {item["id"] for item in second.json()["items"]}
    )


def test_alert_detail_and_review_routes_follow_contract(alert_client: TestClient) -> None:
    now = datetime.now(UTC)
    created = alert_client.post("/api/v1/transactions", json=_transaction(uuid.uuid4(), now))
    alert_id = created.json()["alertId"]

    detail = alert_client.get(f"/api/v1/alerts/{alert_id}")
    status_response = alert_client.patch(f"/api/v1/alerts/{alert_id}", json={"status": "in_review"})
    decision = alert_client.post(
        f"/api/v1/alerts/{alert_id}/decisions",
        json={"outcome": "needs_review", "note": "Check device history"},
    )

    assert detail.status_code == 200
    assert detail.json()["explanationDisclaimer"].endswith("proof or cause of fraud.")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "in_review"
    assert decision.status_code == 201
    assert decision.json()["reviewerRef"] == "demo-analyst"


def test_alert_queue_rejects_invalid_cursor(alert_client: TestClient) -> None:
    now = datetime.now(UTC)
    response = alert_client.get(
        "/api/v1/alerts",
        params={
            "start": (now - timedelta(days=1)).isoformat(),
            "end": (now + timedelta(days=1)).isoformat(),
            "cursor": "invalid",
        },
    )
    assert response.status_code == 422
