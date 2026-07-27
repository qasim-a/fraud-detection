import uuid
from datetime import UTC, datetime

from fraud_api.db.models import AlertRecord, FraudScoreRecord
from fraud_api.db.review_models import AlertHistoryRecord, ReviewDecisionRecord
from fraud_api.repositories.alerts import get_alert_detail
from fraud_api.schemas.alerts import ReviewDecisionInput
from fraud_api.schemas.transactions import TransactionInput
from fraud_api.services.ingestion import IngestionService
from fraud_api.services.reviews import record_decision, update_alert_status
from sqlalchemy import func, select
from sqlalchemy.orm import Session


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


def test_decisions_are_append_only_and_score_is_immutable(
    session: Session, references, model_provider
) -> None:
    account, merchant = references
    result = (
        IngestionService(session, model_provider)
        .ingest(transaction_input(account.id, merchant.id))
        .result
    )
    assert result.alert_id is not None
    original_score = session.scalar(select(FraudScoreRecord))
    assert original_score is not None
    original_probability = original_score.probability

    update_alert_status(session, result.alert_id, "in_review")
    record_decision(
        session,
        result.alert_id,
        ReviewDecisionInput(outcome="needs_review", note="Escalate"),
    )
    record_decision(
        session,
        result.alert_id,
        ReviewDecisionInput(outcome="confirmed_fraud", note="Pattern confirmed"),
    )
    update_alert_status(session, result.alert_id, "closed")

    detail = get_alert_detail(session, result.alert_id)
    assert [decision.outcome for decision in detail.decisions] == [
        "needs_review",
        "confirmed_fraud",
    ]
    assert len(detail.history) == 5
    assert session.scalar(select(func.count()).select_from(ReviewDecisionRecord)) == 2
    assert session.scalar(select(func.count()).select_from(AlertHistoryRecord)) == 5
    assert session.scalar(select(FraudScoreRecord)).probability == original_probability
    assert session.scalar(select(AlertRecord)).status == "closed"
