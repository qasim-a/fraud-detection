"""Fraud score calculation, banding, and explanation mapping."""

from dataclasses import dataclass

from fraud_api.db.models import RiskBand
from fraud_api.features.definitions import FEATURES
from fraud_api.models.loader import ModelBundle
from fraud_api.schemas.transactions import ExplanationFactor

DISPLAY_LABELS = {
    "amount": "Transaction amount",
    "hour_sin": "Time of day (sine)",
    "hour_cos": "Time of day (cosine)",
    "account_tx_count_1h": "Recent transaction frequency",
    "account_avg_amount_30d": "Typical account amount",
    "amount_to_avg_ratio": "Amount compared with account average",
    "country_mismatch": "Country differs from account home",
    "merchant_risk_score": "Merchant risk tier",
}


@dataclass(frozen=True, slots=True)
class ScoreOutcome:
    probability: float
    risk_band: RiskBand
    threshold: float
    factors: list[ExplanationFactor]

    @property
    def creates_alert(self) -> bool:
        return self.probability >= self.threshold


def risk_band(probability: float) -> RiskBand:
    if probability < 0.3:
        return RiskBand.LOW
    if probability < 0.7:
        return RiskBand.MEDIUM
    if probability < 0.9:
        return RiskBand.HIGH
    return RiskBand.CRITICAL


def explanation_factors(contributions: list[float], limit: int = 10) -> list[ExplanationFactor]:
    if len(contributions) != len(FEATURES):
        raise ValueError("Contribution count does not match the feature contract")
    ranked = sorted(
        zip(FEATURES, contributions, strict=True), key=lambda item: abs(item[1]), reverse=True
    )
    return [
        ExplanationFactor(
            feature=feature.name,
            label=DISPLAY_LABELS[feature.name],
            direction="higher" if contribution >= 0 else "lower",
            contribution=contribution,
        )
        for feature, contribution in ranked[:limit]
    ]


def score_features(bundle: ModelBundle, features: dict[str, float | int]) -> ScoreOutcome:
    probability = bundle.predictor.predict_probability(features)
    if not 0 <= probability <= 1:
        raise ValueError("Model probability is outside [0, 1]")
    contributions = bundle.predictor.predict_contributions(features)
    return ScoreOutcome(
        probability=probability,
        risk_band=risk_band(probability),
        threshold=bundle.metadata.threshold,
        factors=explanation_factors(contributions),
    )
