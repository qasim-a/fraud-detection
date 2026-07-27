"""Strict transaction ingestion and scoring contracts."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

CountryCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")]
CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


class TransactionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: uuid.UUID
    event_time: datetime = Field(alias="eventTime")
    account_id: uuid.UUID = Field(alias="accountId")
    merchant_id: uuid.UUID = Field(alias="merchantId")
    amount: Decimal = Field(gt=0, le=Decimal("10000000.00"), decimal_places=2)
    currency: CurrencyCode
    channel: Literal["card_present", "ecommerce", "wallet", "atm"]
    country: CountryCode
    region: str = Field(min_length=1, max_length=64)
    device_id: str = Field(alias="deviceId", min_length=1, max_length=128)
    ip_hash: str = Field(alias="ipHash", min_length=16, max_length=128)

    @field_validator("event_time")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("eventTime must include a timezone offset")
        return value


class ExplanationFactor(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    feature: str
    label: str
    direction: Literal["higher", "lower"]
    contribution: float


def _empty_factors() -> list[ExplanationFactor]:
    return []


class FraudScore(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: uuid.UUID
    probability: float = Field(ge=0, le=1)
    risk_band: Literal["low", "medium", "high", "critical"] = Field(alias="riskBand")
    threshold: float = Field(ge=0, le=1)
    model_version: str = Field(alias="modelVersion")
    feature_version: str = Field(alias="featureVersion")
    scored_at: datetime = Field(alias="scoredAt")
    explanation_status: Literal["available", "unavailable"] = Field(alias="explanationStatus")
    factors: list[ExplanationFactor] = Field(default_factory=_empty_factors)


class TransactionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    transaction_id: uuid.UUID = Field(alias="transactionId")
    status: Literal["scored", "scoring_failed"]
    ingested_at: datetime = Field(alias="ingestedAt")
    score: FraudScore | None = None
    alert_id: uuid.UUID | None = Field(default=None, alias="alertId")
    failure_code: str | None = Field(default=None, alias="failureCode")
