import json
from collections.abc import Callable, Generator
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
def client(
    engine: Engine, model_provider: Callable[[], ModelBundle]
) -> Generator[TestClient, None, None]:
    with Session(engine) as seed_session:
        seed_reference_data(seed_session)
        seed_session.commit()
    app = create_app()

    def session_override() -> Generator[Session, None, None]:
        with Session(engine, expire_on_commit=False) as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    app.dependency_overrides[get_session] = session_override
    app.dependency_overrides[get_model_provider] = lambda: model_provider
    with TestClient(app) as test_client:
        yield test_client


def fixture_payload() -> dict[str, object]:
    return json.loads(Path("tests/fixtures/transaction.json").read_text())


def test_post_get_and_retry_follow_transaction_contract(client: TestClient) -> None:
    payload = fixture_payload()

    created = client.post("/api/v1/transactions", json=payload)
    fetched = client.get(f"/api/v1/transactions/{payload['id']}")
    retried = client.post("/api/v1/transactions", json=payload)

    assert created.status_code == 201
    assert fetched.status_code == 200
    assert retried.status_code == 200
    assert created.json() == fetched.json() == retried.json()
    assert created.json()["score"]["modelVersion"] == "test-v1"
    assert created.json()["alertId"] is not None


def test_conflicting_payload_returns_problem_details(client: TestClient) -> None:
    payload = fixture_payload()
    assert client.post("/api/v1/transactions", json=payload).status_code == 201
    payload["amount"] = "801.00"

    response = client.post("/api/v1/transactions", json=payload)

    assert response.status_code == 409
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["status"] == 409


def test_invalid_transaction_returns_field_errors(client: TestClient) -> None:
    payload = fixture_payload()
    payload["currency"] = "usd"

    response = client.post("/api/v1/transactions", json=payload)

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["errors"][0]["field"].endswith("currency")


def test_get_unknown_transaction_returns_problem_details(client: TestClient) -> None:
    response = client.get("/api/v1/transactions/11111111-1111-4111-8111-111111111111")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
