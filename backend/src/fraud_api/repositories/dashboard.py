"""Exactly reconciled dashboard aggregates over one UTC event-time range."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fraud_api.db.models import (
    AlertRecord,
    FraudScoreRecord,
    ModelStatus,
    ModelVersionRecord,
    TransactionRecord,
)
from fraud_api.db.review_models import ReviewDecisionRecord
from fraud_api.schemas.dashboard import (
    DashboardSummary,
    DashboardTotals,
    ModelMetrics,
    ModelSummary,
    TimeBucket,
    UtcRange,
)


class ActiveModelNotFoundError(RuntimeError):
    """No active model is registered."""


class ModelMetricsUnavailableError(RuntimeError):
    """The active model lacks a complete labeled evaluation."""


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def dashboard_summary(session: Session, start: datetime, end: datetime) -> DashboardSummary:
    in_range = (TransactionRecord.event_time >= start, TransactionRecord.event_time < end)
    transactions = int(
        session.scalar(select(func.count(TransactionRecord.id)).where(*in_range)) or 0
    )
    alert_join = (
        select(AlertRecord.id, TransactionRecord.amount)
        .join(FraudScoreRecord, AlertRecord.fraud_score_id == FraudScoreRecord.id)
        .join(TransactionRecord, FraudScoreRecord.transaction_id == TransactionRecord.id)
        .where(*in_range)
        .subquery()
    )
    alert_count, amount = session.execute(
        select(func.count(alert_join.c.id), func.coalesce(func.sum(alert_join.c.amount), 0))
    ).one()
    band_rows = session.execute(
        select(FraudScoreRecord.risk_band, func.count(FraudScoreRecord.id))
        .join(TransactionRecord, FraudScoreRecord.transaction_id == TransactionRecord.id)
        .where(*in_range)
        .group_by(FraudScoreRecord.risk_band)
    ).all()
    risk_bands = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    risk_bands.update({band.value: int(count) for band, count in band_rows})

    latest_times = (
        select(
            ReviewDecisionRecord.alert_id,
            func.max(ReviewDecisionRecord.created_at).label("created_at"),
        )
        .group_by(ReviewDecisionRecord.alert_id)
        .subquery()
    )
    outcome_rows = session.execute(
        select(ReviewDecisionRecord.outcome, func.count(ReviewDecisionRecord.id))
        .join(
            latest_times,
            (ReviewDecisionRecord.alert_id == latest_times.c.alert_id)
            & (ReviewDecisionRecord.created_at == latest_times.c.created_at),
        )
        .join(AlertRecord, ReviewDecisionRecord.alert_id == AlertRecord.id)
        .join(FraudScoreRecord, AlertRecord.fraud_score_id == FraudScoreRecord.id)
        .join(TransactionRecord, FraudScoreRecord.transaction_id == TransactionRecord.id)
        .where(*in_range)
        .group_by(ReviewDecisionRecord.outcome)
    ).all()
    review_outcomes = {
        "confirmed_fraud": 0,
        "legitimate": 0,
        "needs_review": 0,
        "unlabeled": int(alert_count),
    }
    for outcome, count in outcome_rows:
        review_outcomes[outcome.value] = int(count)
        review_outcomes["unlabeled"] -= int(count)

    transaction_day_rows = session.execute(
        select(func.date(TransactionRecord.event_time), func.count(TransactionRecord.id))
        .where(*in_range)
        .group_by(func.date(TransactionRecord.event_time))
    ).all()
    transaction_days = {str(day): int(count) for day, count in transaction_day_rows}
    alert_day_rows = session.execute(
        select(func.date(TransactionRecord.event_time), func.count(AlertRecord.id))
        .join(FraudScoreRecord, AlertRecord.fraud_score_id == FraudScoreRecord.id)
        .join(TransactionRecord, FraudScoreRecord.transaction_id == TransactionRecord.id)
        .where(*in_range)
        .group_by(func.date(TransactionRecord.event_time))
    ).all()
    alert_days = {str(day): int(count) for day, count in alert_day_rows}
    series = [
        TimeBucket(
            bucket=datetime.fromisoformat(day).replace(tzinfo=UTC),
            transactions=int(transaction_days.get(day, 0)),
            alerts=int(alert_days.get(day, 0)),
        )
        for day in sorted(set(transaction_days) | set(alert_days))
    ]
    return DashboardSummary(
        range=UtcRange(start=start, end=end),
        totals=DashboardTotals(
            transactions=transactions, alerts=int(alert_count), amountAtRisk=Decimal(amount)
        ),
        riskBands=risk_bands,
        reviewOutcomes=review_outcomes,
        series=series,
    )


def active_model_summary(session: Session) -> ModelSummary:
    model = session.scalar(
        select(ModelVersionRecord).where(ModelVersionRecord.status == ModelStatus.ACTIVE)
    )
    if model is None or model.activated_at is None:
        raise ActiveModelNotFoundError("No active model is registered")
    required = {
        "precision",
        "recall",
        "pr_auc",
        "true_positive",
        "false_positive",
        "true_negative",
        "false_negative",
        "alert_volume",
    }
    if not required.issubset(model.metrics):
        raise ModelMetricsUnavailableError("Active model has no complete labeled evaluation")
    return ModelSummary(
        version=model.version,
        featureVersion=model.feature_version,
        datasetId=model.dataset_id,
        threshold=float(model.threshold),
        metrics=ModelMetrics(
            precision=float(model.metrics["precision"]),
            recall=float(model.metrics["recall"]),
            prAuc=float(model.metrics["pr_auc"]),
            truePositive=int(model.metrics["true_positive"]),
            falsePositive=int(model.metrics["false_positive"]),
            trueNegative=int(model.metrics["true_negative"]),
            falseNegative=int(model.metrics["false_negative"]),
            alertVolume=int(model.metrics["alert_volume"]),
        ),
        activatedAt=_utc(model.activated_at),
    )
