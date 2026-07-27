from datetime import UTC, datetime
from decimal import Decimal

from fraud_pipelines.jobs.validation import validate_transactions
from fraud_pipelines.schemas.raw import ACCOUNT_SCHEMA, MERCHANT_SCHEMA, TRANSACTION_SCHEMA


def test_validation_quarantines_duplicates_and_bad_references(spark) -> None:
    account = ("a1", "ACC-1", "US", "NY", datetime(2020, 1, 1, tzinfo=UTC), "consumer")
    merchant = ("m1", "MER-1", "5411", "US", "NY", "low")
    base = (
        "t1",
        "a1",
        "m1",
        datetime(2026, 1, 1, tzinfo=UTC),
        Decimal("10.00"),
        "USD",
        "ecommerce",
        "US",
        "NY",
        "d1",
        "0" * 64,
        False,
        "normal",
    )
    invalid = (
        "t2",
        "missing",
        "m1",
        datetime(2026, 1, 1, tzinfo=UTC),
        Decimal("10.00"),
        "USD",
        "ecommerce",
        "US",
        "NY",
        "d2",
        "1" * 64,
        False,
        "normal",
    )
    result = validate_transactions(
        spark.createDataFrame([base, base, invalid], TRANSACTION_SCHEMA),
        spark.createDataFrame([account], ACCOUNT_SCHEMA),
        spark.createDataFrame([merchant], MERCHANT_SCHEMA),
    )
    assert result.valid.count() == 1
    assert {row.quarantine_reason for row in result.quarantine.collect()} == {
        "duplicate_transaction",
        "unknown_account",
    }
