"""Reusable Spark data-quality rules with explicit quarantine reasons."""

from dataclasses import dataclass

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


@dataclass(frozen=True, slots=True)
class ValidationResult:
    valid: DataFrame
    quarantine: DataFrame


def validate_transactions(
    transactions: DataFrame, accounts: DataFrame, merchants: DataFrame
) -> ValidationResult:
    ranked = transactions.withColumn(
        "_duplicate_rank", F.row_number().over(Window.partitionBy("id").orderBy("event_time", "id"))
    )
    account_ids = accounts.select(F.col("id").alias("_account_id"))
    merchant_ids = merchants.select(F.col("id").alias("_merchant_id"))
    checked = (
        ranked.join(account_ids, ranked.account_id == account_ids._account_id, "left")
        .join(merchant_ids, ranked.merchant_id == merchant_ids._merchant_id, "left")
        .withColumn(
            "quarantine_reason",
            F.when(F.col("_duplicate_rank") > 1, "duplicate_transaction")
            .when(F.col("amount") <= 0, "invalid_amount")
            .when(~F.col("currency").isin("USD", "GBP", "CAD", "EUR"), "unsupported_currency")
            .when(F.col("_account_id").isNull(), "unknown_account")
            .when(F.col("_merchant_id").isNull(), "unknown_merchant"),
        )
    )
    clean = checked.drop("_duplicate_rank", "_account_id", "_merchant_id")
    return ValidationResult(
        valid=clean.where(F.col("quarantine_reason").isNull()).drop("quarantine_reason"),
        quarantine=clean.where(F.col("quarantine_reason").isNotNull()),
    )
