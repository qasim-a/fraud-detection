import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from fraud_api.features.online import OnlineFeatureContext, build_online_features
from fraud_api.schemas.transactions import TransactionInput


@pytest.mark.parametrize("case_index", [0, 1])
def test_online_features_match_golden_batch_values(case_index: int) -> None:
    case = json.loads(Path("tests/fixtures/feature_parity.json").read_text())["cases"][case_index]
    inputs = case["input"]
    event_time = datetime.fromisoformat(inputs["event_time"].replace("Z", "+00:00"))
    transaction = TransactionInput(
        id="11111111-1111-4111-8111-111111111111",
        eventTime=event_time,
        accountId="22222222-2222-4222-8222-222222222222",
        merchantId="33333333-3333-4333-8333-333333333333",
        amount=Decimal(str(inputs["amount"])),
        currency="USD",
        channel="ecommerce",
        country=inputs["transaction_country"],
        region="demo",
        deviceId="device_demo_001",
        ipHash="0123456789abcdef",
    )
    context = OnlineFeatureContext(
        account_tx_count_1h=inputs["account_tx_count_1h"],
        account_avg_amount_30d=inputs["account_avg_amount_30d"],
        account_country=inputs["account_country"],
        merchant_risk_score=inputs["merchant_risk_score"],
        source_as_of=event_time,
    )

    actual = build_online_features(transaction, context)

    assert actual == pytest.approx(case["expected"], abs=1e-6)
