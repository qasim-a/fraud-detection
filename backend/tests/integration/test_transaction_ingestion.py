import uuid
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from fraud_api.db.models import AlertRecord, FraudScoreRecord, TransactionRecord
from fraud_api.models.loader import ModelBundle, ModelUnavailableError, Predictor
from fraud_api.repositories.transactions import TransactionConflictError
from fraud_api.schemas.transactions import TransactionInput
from fraud_api.services.ingestion import IngestionService
from sqlalchemy import func, select
from sqlalchemy.orm import Session

pytestmark = pytest.mark.integration


def transaction_input(account_id: uuid.UUID, merchant_id: uuid.UUID) -> TransactionInput:
    return TransactionInput(
        id=uuid.UUID("42b45983-a29d-49f4-8582-7e31cdde30b2"),
        eventTime=datetime(2026, 7, 27, 14, 30, tzinfo=UTC),
        accountId=account_id,
        merchantId=merchant_id,
        amount="800.00",
        currency="USD",
        channel="ecommerce",
        country="GB",
        region="LND",
        deviceId="device_demo_001",
        ipHash="0123456789abcdef0123456789abcdef",
    )


def count(session: Session, model: type) -> int:
    return int(session.scalar(select(func.count()).select_from(model)) or 0)


def test_identical_retry_returns_original_without_duplicates(
    session: Session, references, model_provider
) -> None:
    account, merchant = references
    payload = transaction_input(account.id, merchant.id)
    service = IngestionService(session, model_provider)

    first = service.ingest(payload)
    second = service.ingest(payload)

    assert first.created is True
    assert second.created is False
    assert first.result == second.result
    assert count(session, TransactionRecord) == 1
    assert count(session, FraudScoreRecord) == 1
    assert count(session, AlertRecord) == 1


def test_changed_payload_with_same_id_is_conflict(
    session: Session, references, model_provider
) -> None:
    account, merchant = references
    payload = transaction_input(account.id, merchant.id)
    service = IngestionService(session, model_provider)
    service.ingest(payload)

    with pytest.raises(TransactionConflictError):
        service.ingest(payload.model_copy(update={"amount": payload.amount + 1}))

    assert count(session, TransactionRecord) == 1


def test_model_unavailable_persists_explicit_failure(session: Session, references) -> None:
    account, merchant = references
    payload = transaction_input(account.id, merchant.id)

    def unavailable() -> ModelBundle:
        raise ModelUnavailableError("missing")

    result = IngestionService(session, unavailable).ingest(payload).result

    assert result.status == "scoring_failed"
    assert result.failure_code == "model_unavailable"
    assert result.score is None
    assert count(session, FraudScoreRecord) == 0


class BrokenPredictor(Predictor):
    def predict_probability(self, _features: dict[str, float | int]) -> float:
        raise ValueError("unexpected model failure")

    def predict_contributions(self, _features: dict[str, float | int]) -> list[float]:
        return []


def test_unexpected_scoring_error_can_be_rolled_back_atomically(
    session: Session, references, model_bundle: ModelBundle
) -> None:
    account, merchant = references
    payload = transaction_input(account.id, merchant.id)
    broken = replace(model_bundle, predictor=BrokenPredictor())

    with pytest.raises(ValueError, match="unexpected model failure"):
        IngestionService(session, lambda: broken).ingest(payload)
    session.rollback()

    assert count(session, TransactionRecord) == 0
    assert count(session, FraudScoreRecord) == 0
