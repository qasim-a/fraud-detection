"""Append-only analyst review and alert audit models."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from fraud_api.db.models import AlertStatus, enum_type
from fraud_api.db.session import Base


class ReviewOutcome(enum.StrEnum):
    CONFIRMED_FRAUD = "confirmed_fraud"
    LEGITIMATE = "legitimate"
    NEEDS_REVIEW = "needs_review"


class HistoryEventType(enum.StrEnum):
    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    DECISION_RECORDED = "decision_recorded"
    REOPENED = "reopened"


class ReviewDecisionRecord(Base):
    __tablename__ = "review_decisions"
    __table_args__ = (Index("ix_review_decisions_alert_created", "alert_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    alert_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("alerts.id"), nullable=False)
    outcome: Mapped[ReviewOutcome] = mapped_column(enum_type(ReviewOutcome, "review_outcome"))
    note: Mapped[str | None] = mapped_column(Text)
    reviewer_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AlertHistoryRecord(Base):
    __tablename__ = "alert_history"
    __table_args__ = (Index("ix_alert_history_alert_created", "alert_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    alert_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("alerts.id"), nullable=False)
    event_type: Mapped[HistoryEventType] = mapped_column(
        enum_type(HistoryEventType, "history_event_type")
    )
    from_status: Mapped[AlertStatus | None] = mapped_column(
        enum_type(AlertStatus, "alert_status_from")
    )
    to_status: Mapped[AlertStatus | None] = mapped_column(enum_type(AlertStatus, "alert_status_to"))
    review_decision_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("review_decisions.id"))
    actor_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
