"""Public alert investigation schemas."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from fraud_api.db.models import AlertStatus, RiskBand
from fraud_api.db.review_models import HistoryEventType, ReviewOutcome
from fraud_api.schemas.transactions import FraudScore, TransactionInput


class AlertSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class AlertSummary(AlertSchema):
    id: uuid.UUID
    transaction_id: uuid.UUID = Field(alias="transactionId")
    probability: float = Field(ge=0, le=1)
    risk_band: RiskBand = Field(alias="riskBand")
    amount: Decimal
    currency: str
    merchant_ref: str = Field(alias="merchantRef")
    channel: str
    country: str
    status: AlertStatus
    created_at: datetime = Field(alias="createdAt")


class AlertPage(AlertSchema):
    items: list[AlertSummary]
    next_cursor: str | None = Field(default=None, alias="nextCursor")


class ReviewDecisionInput(AlertSchema):
    outcome: ReviewOutcome
    note: str | None = Field(default=None, max_length=2000)


class ReviewDecision(AlertSchema):
    id: uuid.UUID
    alert_id: uuid.UUID = Field(alias="alertId")
    outcome: ReviewOutcome
    note: str | None
    reviewer_ref: str = Field(alias="reviewerRef")
    created_at: datetime = Field(alias="createdAt")


class HistoryEvent(AlertSchema):
    id: uuid.UUID
    event_type: HistoryEventType = Field(alias="eventType")
    from_status: AlertStatus | None = Field(alias="fromStatus")
    to_status: AlertStatus | None = Field(alias="toStatus")
    actor_ref: str = Field(alias="actorRef")
    created_at: datetime = Field(alias="createdAt")


class AlertDetail(AlertSummary):
    transaction: TransactionInput
    score: FraudScore
    history: list[HistoryEvent]
    decisions: list[ReviewDecision]
    explanation_disclaimer: str = Field(
        alias="explanationDisclaimer",
        default=("Model factors indicate statistical influence, not proof or cause of fraud."),
    )


class AlertStatusInput(AlertSchema):
    status: AlertStatus
