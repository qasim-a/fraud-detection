from fraud_api.db.models import RiskBand
from fraud_api.services.scoring import explanation_factors, risk_band, score_features


def test_risk_band_boundaries_are_deterministic() -> None:
    assert risk_band(0.299999) is RiskBand.LOW
    assert risk_band(0.3) is RiskBand.MEDIUM
    assert risk_band(0.7) is RiskBand.HIGH
    assert risk_band(0.9) is RiskBand.CRITICAL


def test_explanations_are_ranked_and_directional() -> None:
    factors = explanation_factors([0.1, -0.9, 0.3, 0.2, -0.4, 0.8, 0.5, 0.6], limit=3)

    assert [factor.feature for factor in factors] == [
        "hour_sin",
        "amount_to_avg_ratio",
        "merchant_risk_score",
    ]
    assert [factor.direction for factor in factors] == ["lower", "higher", "higher"]


def test_probability_equal_to_threshold_creates_alert(model_bundle) -> None:
    model_bundle.predictor.probability = 0.8
    outcome = score_features(model_bundle, {"amount": 10.0})

    assert outcome.creates_alert is True
    assert outcome.risk_band is RiskBand.HIGH
