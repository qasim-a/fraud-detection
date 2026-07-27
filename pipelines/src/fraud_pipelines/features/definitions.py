"""Spark-side mirror of the scoring feature contract."""

from dataclasses import asdict, dataclass
from typing import Literal

FEATURE_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class FeatureDefinition:
    name: str
    data_type: Literal["float", "integer"]
    default: float | int
    minimum: float
    maximum: float
    description: str

    def as_dict(self) -> dict[str, str | float | int]:
        return asdict(self)


FEATURES = (
    FeatureDefinition("amount", "float", 0.0, 0.0, 10_000_000.0, "Transaction amount"),
    FeatureDefinition("hour_sin", "float", 0.0, -1.0, 1.0, "Cyclical event hour sine"),
    FeatureDefinition("hour_cos", "float", 1.0, -1.0, 1.0, "Cyclical event hour cosine"),
    FeatureDefinition(
        "account_tx_count_1h",
        "integer",
        0,
        0.0,
        100_000.0,
        "Prior account transactions in one hour",
    ),
    FeatureDefinition(
        "account_avg_amount_30d",
        "float",
        0.0,
        0.0,
        10_000_000.0,
        "Prior 30-day account mean amount",
    ),
    FeatureDefinition(
        "amount_to_avg_ratio", "float", 1.0, 0.0, 100_000.0, "Amount divided by prior account mean"
    ),
    FeatureDefinition(
        "country_mismatch", "integer", 0, 0.0, 1.0, "Transaction country differs from account home"
    ),
    FeatureDefinition(
        "merchant_risk_score", "float", 0.0, 0.0, 1.0, "Versioned merchant risk input"
    ),
)

FEATURE_BY_NAME = {feature.name: feature for feature in FEATURES}
