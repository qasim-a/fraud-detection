from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fraud_pipelines.jobs.features import build_features
from fraud_pipelines.schemas.raw import ACCOUNT_SCHEMA, MERCHANT_SCHEMA, TRANSACTION_SCHEMA

pytestmark = pytest.mark.integration


def test_features_use_only_prior_account_history(spark) -> None:
    account = ("a1", "ACC-1", "US", "NY", datetime(2020, 1, 1, tzinfo=UTC), "consumer")
    merchant = ("m1", "MER-1", "5411", "US", "NY", "medium")
    start = datetime(2026, 1, 1, tzinfo=UTC)

    def transaction(identifier, at, amount):
        return (
            identifier,
            "a1",
            "m1",
            at,
            Decimal(amount),
            "USD",
            "ecommerce",
            "US",
            "NY",
            "d1",
            "0" * 64,
            False,
            "normal",
        )

    rows = [
        transaction("t1", start, "10.00"),
        transaction("t2", start + timedelta(minutes=30), "30.00"),
        transaction("t3", start + timedelta(hours=2), "90.00"),
    ]
    result = (
        build_features(
            spark.createDataFrame(rows, TRANSACTION_SCHEMA),
            spark.createDataFrame([account], ACCOUNT_SCHEMA),
            spark.createDataFrame([merchant], MERCHANT_SCHEMA),
        )
        .orderBy("event_time")
        .collect()
    )
    assert [row.account_tx_count_1h for row in result] == [0, 1, 0]
    assert [round(row.account_avg_amount_30d, 2) for row in result] == [0.0, 10.0, 20.0]
    assert round(result[2].amount_to_avg_ratio, 2) == 4.5
