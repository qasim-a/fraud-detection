"""Versioned raw input schemas for deterministic Spark ingestion."""

from pyspark.sql.types import (
    BooleanType,
    DecimalType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

SCHEMA_VERSION = "1.0.0"

ACCOUNT_SCHEMA = StructType(
    [
        StructField("id", StringType(), False),
        StructField("external_ref", StringType(), False),
        StructField("home_country", StringType(), False),
        StructField("home_region", StringType(), False),
        StructField("opened_at", TimestampType(), False),
        StructField("segment", StringType(), False),
    ]
)
MERCHANT_SCHEMA = StructType(
    [
        StructField("id", StringType(), False),
        StructField("external_ref", StringType(), False),
        StructField("category_code", StringType(), False),
        StructField("country", StringType(), False),
        StructField("region", StringType(), False),
        StructField("risk_tier", StringType(), False),
    ]
)
TRANSACTION_SCHEMA = StructType(
    [
        StructField("id", StringType(), False),
        StructField("account_id", StringType(), False),
        StructField("merchant_id", StringType(), False),
        StructField("event_time", TimestampType(), False),
        StructField("amount", DecimalType(18, 2), False),
        StructField("currency", StringType(), False),
        StructField("channel", StringType(), False),
        StructField("country", StringType(), False),
        StructField("region", StringType(), False),
        StructField("device_id", StringType(), False),
        StructField("ip_hash", StringType(), False),
        StructField("is_fraud", BooleanType(), False),
        StructField("scenario", StringType(), False),
    ]
)
