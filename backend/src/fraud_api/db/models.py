"""Operational persistence models for scoring and alert creation."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from fraud_api.db.session import Base


class AccountSegment(enum.StrEnum):
    CONSUMER = "consumer"
    SMALL_BUSINESS = "small_business"


class MerchantRiskTier(enum.StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TransactionStatus(enum.StrEnum):
    ACCEPTED = "accepted"
    SCORED = "scored"
    SCORING_FAILED = "scoring_failed"


class ModelStatus(enum.StrEnum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    RETIRED = "retired"


class RiskBand(enum.StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExplanationStatus(enum.StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class AlertStatus(enum.StrEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    CLOSED = "closed"


def enum_values(values: type[enum.Enum]) -> list[str]:
    return [str(value.value) for value in values]


def enum_type(enum_class: type[enum.Enum], name: str) -> Enum:
    return Enum(
        enum_class,
        name=name,
        native_enum=False,
        values_callable=enum_values,
    )


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    external_ref: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    home_country: Mapped[str] = mapped_column(String(2), nullable=False)
    home_region: Mapped[str] = mapped_column(String(64), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    segment: Mapped[AccountSegment] = mapped_column(enum_type(AccountSegment, "account_segment"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    external_ref: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    category_code: Mapped[str] = mapped_column(String(4), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    region: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_tier: Mapped[MerchantRiskTier] = mapped_column(
        enum_type(MerchantRiskTier, "merchant_risk_tier")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TransactionRecord(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_event_time", "event_time"),
        Index("ix_transactions_account_event", "account_id", "event_time"),
        Index("ix_transactions_merchant_event", "merchant_id", "event_time"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    merchant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("merchants.id"), nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    region: Mapped[str] = mapped_column(String(64), nullable=False)
    device_id: Mapped[str] = mapped_column(String(128), nullable=False)
    ip_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(
        enum_type(TransactionStatus, "transaction_status")
    )
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(64))
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class FeatureSnapshot(Base):
    __tablename__ = "feature_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transactions.id"), unique=True, nullable=False
    )
    feature_version: Mapped[str] = mapped_column(String(32), nullable=False)
    values: Mapped[dict[str, float | int]] = mapped_column(JSON, nullable=False)
    source_as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ModelVersionRecord(Base):
    __tablename__ = "model_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    feature_version: Mapped[str] = mapped_column(String(32), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(128), nullable=False)
    artifact_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    artifact_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    threshold: Mapped[Decimal] = mapped_column(Numeric(8, 7), nullable=False)
    status: Mapped[ModelStatus] = mapped_column(enum_type(ModelStatus, "model_status"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FraudScoreRecord(Base):
    __tablename__ = "fraud_scores"
    __table_args__ = (
        Index("ix_fraud_scores_probability_time", "probability", "scored_at"),
        Index("ix_fraud_scores_model_time", "model_version_id", "scored_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transactions.id"), unique=True, nullable=False
    )
    feature_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("feature_snapshots.id"), unique=True, nullable=False
    )
    model_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("model_versions.id"), nullable=False
    )
    probability: Mapped[Decimal] = mapped_column(Numeric(8, 7), nullable=False)
    risk_band: Mapped[RiskBand] = mapped_column(enum_type(RiskBand, "risk_band"))
    threshold: Mapped[Decimal] = mapped_column(Numeric(8, 7), nullable=False)
    explanation_status: Mapped[ExplanationStatus] = mapped_column(
        enum_type(ExplanationStatus, "explanation_status")
    )
    explanation_factors: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AlertRecord(Base):
    __tablename__ = "alerts"
    __table_args__ = (Index("ix_alerts_status_created", "status", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fraud_score_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fraud_scores.id"), unique=True, nullable=False
    )
    status: Mapped[AlertStatus] = mapped_column(enum_type(AlertStatus, "alert_status"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
