import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fraud_api.db.models import ModelVersionRecord
from fraud_api.repositories.dashboard import (
    ModelMetricsUnavailableError,
    active_model_summary,
    dashboard_summary,
)
from fraud_api.schemas.alerts import ReviewDecisionInput
from fraud_api.schemas.transactions import TransactionInput
from fraud_api.services.ingestion import IngestionService
from fraud_api.services.reviews import record_decision
from sqlalchemy import select
from sqlalchemy.orm import Session


def _input(account_id: uuid.UUID, merchant_id: uuid.UUID, identifier: uuid.UUID, at: datetime):
    return TransactionInput(
        id=identifier,
        eventTime=at,
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


def test_dashboard_aggregates_reconcile_and_preserve_unlabeled(
    session: Session, references, model_provider
) -> None:
    account, merchant = references
    start = datetime(2026, 7, 27, tzinfo=UTC)
    first = (
        IngestionService(session, model_provider)
        .ingest(_input(account.id, merchant.id, uuid.uuid4(), start + timedelta(hours=1)))
        .result
    )
    second = (
        IngestionService(session, model_provider)
        .ingest(_input(account.id, merchant.id, uuid.uuid4(), start + timedelta(hours=2)))
        .result
    )
    assert first.alert_id is not None and second.alert_id is not None
    record_decision(session, first.alert_id, ReviewDecisionInput(outcome="legitimate", note=None))

    result = dashboard_summary(session, start, start + timedelta(days=1))

    assert result.totals.transactions == 2
    assert result.totals.alerts == 2
    assert result.totals.amount_at_risk == 1600
    assert result.risk_bands["critical"] == 2
    assert result.review_outcomes["legitimate"] == 1
    assert result.review_outcomes["unlabeled"] == 1
    assert result.series[0].transactions == result.series[0].alerts == 2


def test_active_model_refuses_incomplete_unlabeled_metrics(
    session: Session, references, model_provider
) -> None:
    account, merchant = references
    IngestionService(session, model_provider).ingest(
        _input(account.id, merchant.id, uuid.uuid4(), datetime(2026, 7, 27, tzinfo=UTC))
    )
    with pytest.raises(ModelMetricsUnavailableError):
        active_model_summary(session)

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
    assert active_model_summary(session).metrics.true_positive == 7
