from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fraud_pipelines.jobs.features import build_features
from fraud_pipelines.jobs.manifests import write_feature_dataset
from fraud_pipelines.schemas.raw import ACCOUNT_SCHEMA, MERCHANT_SCHEMA, TRANSACTION_SCHEMA

pytestmark = pytest.mark.integration


def test_repeated_feature_writes_have_same_identity_and_values(spark, tmp_path) -> None:
    account = ("a1", "ACC-1", "US", "NY", datetime(2020, 1, 1, tzinfo=UTC), "consumer")
    merchant = ("m1", "MER-1", "5411", "US", "NY", "low")
    transaction = (
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
    frame = build_features(
        spark.createDataFrame([transaction], TRANSACTION_SCHEMA),
        spark.createDataFrame([account], ACCOUNT_SCHEMA),
        spark.createDataFrame([merchant], MERCHANT_SCHEMA),
    )
    source = {"dataset_id": "source-1"}
    first = write_feature_dataset(frame, tmp_path / "first", source, 1)
    second = write_feature_dataset(frame, tmp_path / "second", source, 1)
    assert first["dataset_id"] == second["dataset_id"]
    assert (
        spark.read.parquet(first["output_uri"]).collect()
        == spark.read.parquet(second["output_uri"]).collect()
    )
