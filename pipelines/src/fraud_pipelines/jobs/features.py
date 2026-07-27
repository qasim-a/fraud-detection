"""Point-in-time Spark features implemented without Python UDFs."""

import math

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

from fraud_pipelines.features.definitions import FEATURE_VERSION


def build_features(transactions: DataFrame, accounts: DataFrame, merchants: DataFrame) -> DataFrame:
    risk_score = F.create_map(
        F.lit("low"), F.lit(0.1), F.lit("medium"), F.lit(0.5), F.lit("high"), F.lit(0.9)
    )
    base = (
        transactions.join(
            accounts.select(F.col("id").alias("account_ref"), "home_country"),
            transactions.account_id == F.col("account_ref"),
        )
        .join(
            merchants.select(F.col("id").alias("merchant_ref"), "risk_tier"),
            transactions.merchant_id == F.col("merchant_ref"),
        )
        .withColumn("_epoch", F.col("event_time").cast("long"))
    )
    account_order = Window.partitionBy("account_id").orderBy("_epoch")
    hour_window = account_order.rangeBetween(-3600, -1)
    month_window = account_order.rangeBetween(-30 * 86400, -1)
    hour = F.hour("event_time").cast("double")
    prior_average = F.avg(F.col("amount").cast("double")).over(month_window)
    return (
        base.withColumn("amount", F.col("amount").cast("double"))
        .withColumn("hour_sin", F.sin(hour * F.lit(2 * math.pi / 24)))
        .withColumn("hour_cos", F.cos(hour * F.lit(2 * math.pi / 24)))
        .withColumn("account_tx_count_1h", F.count("id").over(hour_window).cast("long"))
        .withColumn("account_avg_amount_30d", F.coalesce(prior_average, F.lit(0.0)))
        .withColumn(
            "amount_to_avg_ratio",
            F.when(prior_average > 0, F.col("amount") / prior_average).otherwise(F.lit(1.0)),
        )
        .withColumn("country_mismatch", (F.col("country") != F.col("home_country")).cast("long"))
        .withColumn("merchant_risk_score", risk_score[F.col("risk_tier")])
        .withColumn("feature_version", F.lit(FEATURE_VERSION))
        .drop("account_ref", "merchant_ref", "home_country", "risk_tier", "_epoch")
    )
