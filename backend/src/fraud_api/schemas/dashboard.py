"""Reconciled operational dashboard and model evaluation schemas."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DashboardSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class UtcRange(DashboardSchema):
    start: datetime
    end: datetime


class DashboardTotals(DashboardSchema):
    transactions: int = Field(ge=0)
    alerts: int = Field(ge=0)
    amount_at_risk: Decimal = Field(alias="amountAtRisk", ge=0)


class TimeBucket(DashboardSchema):
    bucket: datetime
    transactions: int = Field(ge=0)
    alerts: int = Field(ge=0)


class DashboardSummary(DashboardSchema):
    range: UtcRange
    totals: DashboardTotals
    risk_bands: dict[str, int] = Field(alias="riskBands")
    review_outcomes: dict[str, int] = Field(alias="reviewOutcomes")
    series: list[TimeBucket]


class ModelMetrics(DashboardSchema):
    precision: float = Field(ge=0, le=1)
    recall: float = Field(ge=0, le=1)
    pr_auc: float = Field(alias="prAuc", ge=0, le=1)
    true_positive: int = Field(alias="truePositive", ge=0)
    false_positive: int = Field(alias="falsePositive", ge=0)
    true_negative: int = Field(alias="trueNegative", ge=0)
    false_negative: int = Field(alias="falseNegative", ge=0)
    alert_volume: int = Field(alias="alertVolume", ge=0)


class ModelSummary(DashboardSchema):
    version: str
    feature_version: str = Field(alias="featureVersion")
    dataset_id: str = Field(alias="datasetId")
    threshold: float = Field(ge=0, le=1)
    metrics: ModelMetrics
    activated_at: datetime = Field(alias="activatedAt")
