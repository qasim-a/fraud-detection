"""Scalar online feature transformations compatible with batch definitions."""

import math
from dataclasses import dataclass
from datetime import datetime

from fraud_api.features.definitions import FEATURE_BY_NAME
from fraud_api.schemas.transactions import TransactionInput


@dataclass(frozen=True, slots=True)
class OnlineFeatureContext:
    account_tx_count_1h: int
    account_avg_amount_30d: float
    account_country: str
    merchant_risk_score: float
    source_as_of: datetime


def build_online_features(
    transaction: TransactionInput,
    context: OnlineFeatureContext,
) -> dict[str, float | int]:
    hour = transaction.event_time.hour + transaction.event_time.minute / 60
    angle = 2 * math.pi * hour / 24
    average = context.account_avg_amount_30d
    ratio = float(transaction.amount) / average if average > 0 else 1.0
    values: dict[str, float | int] = {
        "amount": float(transaction.amount),
        "hour_sin": math.sin(angle),
        "hour_cos": math.cos(angle),
        "account_tx_count_1h": context.account_tx_count_1h,
        "account_avg_amount_30d": average,
        "amount_to_avg_ratio": ratio,
        "country_mismatch": int(transaction.country != context.account_country),
        "merchant_risk_score": context.merchant_risk_score,
    }
    for name, value in values.items():
        definition = FEATURE_BY_NAME[name]
        if (
            not math.isfinite(float(value))
            or not definition.minimum <= float(value) <= definition.maximum
        ):
            raise ValueError(f"Feature {name} is outside its registered bounds")
    return values
