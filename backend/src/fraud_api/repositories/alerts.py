"""Read models and stable cursor queries for analyst alerts."""

import base64
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal, cast

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.orm import Session

from fraud_api.db.models import (
    AlertRecord,
    AlertStatus,
    FraudScoreRecord,
    Merchant,
    ModelVersionRecord,
    TransactionRecord,
)
from fraud_api.db.review_models import AlertHistoryRecord, ReviewDecisionRecord
from fraud_api.schemas.alerts import (
    AlertDetail,
    AlertPage,
    AlertSummary,
    HistoryEvent,
    ReviewDecision,
)
from fraud_api.schemas.transactions import ExplanationFactor, FraudScore, TransactionInput


class AlertNotFoundError(RuntimeError):
    """The requested alert does not exist."""


class InvalidCursorError(ValueError):
    """The supplied cursor is malformed."""


@dataclass(frozen=True, slots=True)
class AlertRow:
    alert: AlertRecord
    score: FraudScoreRecord
    transaction: TransactionRecord
    merchant: Merchant


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def _encode_cursor(row: AlertRow) -> str:
    raw = json.dumps(
        [str(row.score.probability), _utc(row.alert.created_at).isoformat(), str(row.alert.id)],
        separators=(",", ":"),
    ).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _decode_cursor(value: str) -> tuple[Decimal, datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        probability, created_at, alert_id = json.loads(raw)
        return Decimal(probability), datetime.fromisoformat(created_at), uuid.UUID(alert_id)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise InvalidCursorError("Invalid alert cursor") from exc


def _base_query() -> Select[tuple[AlertRecord, FraudScoreRecord, TransactionRecord, Merchant]]:
    return (
        select(AlertRecord, FraudScoreRecord, TransactionRecord, Merchant)
        .join(FraudScoreRecord, AlertRecord.fraud_score_id == FraudScoreRecord.id)
        .join(TransactionRecord, FraudScoreRecord.transaction_id == TransactionRecord.id)
        .join(Merchant, TransactionRecord.merchant_id == Merchant.id)
    )


def _summary(row: AlertRow) -> AlertSummary:
    return AlertSummary(
        id=row.alert.id,
        transactionId=row.transaction.id,
        probability=float(row.score.probability),
        riskBand=row.score.risk_band,
        amount=row.transaction.amount,
        currency=row.transaction.currency,
        merchantRef=row.merchant.external_ref,
        channel=row.transaction.channel,
        country=row.transaction.country,
        status=row.alert.status,
        createdAt=_utc(row.alert.created_at),
    )


def list_alerts(
    session: Session,
    *,
    start: datetime,
    end: datetime,
    status: AlertStatus | None = None,
    min_risk: float | None = None,
    merchant: str | None = None,
    channel: str | None = None,
    country: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> AlertPage:
    query = _base_query().where(AlertRecord.created_at >= start, AlertRecord.created_at < end)
    if status is not None:
        query = query.where(AlertRecord.status == status)
    if min_risk is not None:
        query = query.where(FraudScoreRecord.probability >= min_risk)
    if merchant:
        query = query.where(Merchant.external_ref == merchant)
    if channel:
        query = query.where(TransactionRecord.channel == channel)
    if country:
        query = query.where(TransactionRecord.country == country)
    if cursor:
        probability, created_at, alert_id = _decode_cursor(cursor)
        query = query.where(
            or_(
                FraudScoreRecord.probability < probability,
                and_(
                    FraudScoreRecord.probability == probability,
                    AlertRecord.created_at < created_at,
                ),
                and_(
                    FraudScoreRecord.probability == probability,
                    AlertRecord.created_at == created_at,
                    AlertRecord.id < alert_id,
                ),
            )
        )
    query = query.order_by(
        FraudScoreRecord.probability.desc(), AlertRecord.created_at.desc(), AlertRecord.id.desc()
    ).limit(limit + 1)
    rows = [AlertRow(value[0], value[1], value[2], value[3]) for value in session.execute(query)]
    page_rows = rows[:limit]
    next_cursor = _encode_cursor(page_rows[-1]) if len(rows) > limit else None
    return AlertPage(items=[_summary(row) for row in page_rows], nextCursor=next_cursor)


def get_alert_row(session: Session, alert_id: uuid.UUID) -> AlertRow:
    value = session.execute(_base_query().where(AlertRecord.id == alert_id)).one_or_none()
    if value is None:
        raise AlertNotFoundError(str(alert_id))
    return AlertRow(value[0], value[1], value[2], value[3])


def get_alert_detail(session: Session, alert_id: uuid.UUID) -> AlertDetail:
    row = get_alert_row(session, alert_id)
    model = session.get(ModelVersionRecord, row.score.model_version_id)
    if model is None:
        raise RuntimeError("Alert score references a missing model")
    history = session.scalars(
        select(AlertHistoryRecord)
        .where(AlertHistoryRecord.alert_id == alert_id)
        .order_by(AlertHistoryRecord.created_at, AlertHistoryRecord.id)
    ).all()
    decisions = session.scalars(
        select(ReviewDecisionRecord)
        .where(ReviewDecisionRecord.alert_id == alert_id)
        .order_by(ReviewDecisionRecord.created_at, ReviewDecisionRecord.id)
    ).all()
    summary = _summary(row)
    return AlertDetail(
        **summary.model_dump(),
        transaction=TransactionInput(
            id=row.transaction.id,
            eventTime=_utc(row.transaction.event_time),
            accountId=row.transaction.account_id,
            merchantId=row.transaction.merchant_id,
            amount=row.transaction.amount,
            currency=row.transaction.currency,
            channel=cast(
                Literal["card_present", "ecommerce", "wallet", "atm"], row.transaction.channel
            ),
            country=row.transaction.country,
            region=row.transaction.region,
            deviceId=row.transaction.device_id,
            ipHash=row.transaction.ip_hash,
        ),
        score=FraudScore(
            id=row.score.id,
            probability=float(row.score.probability),
            riskBand=row.score.risk_band.value,
            threshold=float(row.score.threshold),
            modelVersion=model.version,
            featureVersion=model.feature_version,
            scoredAt=_utc(row.score.scored_at),
            explanationStatus=row.score.explanation_status.value,
            factors=[
                ExplanationFactor.model_validate(item) for item in row.score.explanation_factors
            ],
        ),
        history=[HistoryEvent.model_validate(item, from_attributes=True) for item in history],
        decisions=[ReviewDecision.model_validate(item, from_attributes=True) for item in decisions],
    )
