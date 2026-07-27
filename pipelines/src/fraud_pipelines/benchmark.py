"""Repeatable local scale benchmark with environment and lineage evidence."""

import json
import os
import platform
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pyspark.sql import SparkSession

from fraud_pipelines.config import PipelineSettings
from fraud_pipelines.generation.entities import generate_accounts, generate_merchants
from fraud_pipelines.generation.transactions import generate_transactions
from fraud_pipelines.generation.write import write_snapshot
from fraud_pipelines.jobs.features import build_features
from fraud_pipelines.jobs.manifests import write_feature_dataset
from fraud_pipelines.jobs.validation import validate_transactions
from fraud_pipelines.schemas.raw import ACCOUNT_SCHEMA, MERCHANT_SCHEMA, TRANSACTION_SCHEMA


def _directory_size(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def run_benchmark(settings: PipelineSettings, seed: int, rows: int) -> dict[str, Any]:
    if rows < 1:
        raise ValueError("rows must be positive")
    root = settings.artifact_root / "benchmarks" / f"rows-{rows}-seed-{seed}"
    if root.exists():
        shutil.rmtree(root)
    bronze = root / "bronze"
    features = root / "features"
    started = time.perf_counter()
    accounts = generate_accounts(seed, max(100, rows // 20))
    merchants = generate_merchants(seed, max(25, rows // 200))
    transactions = generate_transactions(seed, rows, accounts, merchants)
    source = write_snapshot(
        bronze, seed, {"accounts": accounts, "merchants": merchants, "transactions": transactions}
    )
    generation_seconds = time.perf_counter() - started
    spark = (
        SparkSession.builder.master(settings.spark_master)
        .appName("fraud-benchmark")
        .config("spark.sql.shuffle.partitions", str(settings.spark_shuffle_partitions))
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    try:
        processing_started = time.perf_counter()
        account_frame = spark.read.schema(ACCOUNT_SCHEMA).json(str(bronze / "accounts.jsonl"))
        merchant_frame = spark.read.schema(MERCHANT_SCHEMA).json(str(bronze / "merchants.jsonl"))
        transaction_frame = spark.read.schema(TRANSACTION_SCHEMA).json(
            str(bronze / "transactions.jsonl")
        )
        validated = validate_transactions(transaction_frame, account_frame, merchant_frame)
        manifest = write_feature_dataset(
            build_features(validated.valid, account_frame, merchant_frame), features, source
        )
        rejected = validated.quarantine.count()
        processing_seconds = time.perf_counter() - processing_started
        spark_version = spark.version
    finally:
        spark.stop()
    report = {
        "schema_version": "1.0.0",
        "recorded_at": datetime.now(UTC).isoformat(),
        "seed": seed,
        "requested_rows": rows,
        "processed_rows": manifest["counts"]["rows"],
        "rejected_rows": rejected,
        "generation_seconds": round(generation_seconds, 3),
        "processing_seconds": round(processing_seconds, 3),
        "total_seconds": round(time.perf_counter() - started, 3),
        "output_bytes": _directory_size(features / "data"),
        "input_fingerprint": source["dataset_id"],
        "output_fingerprint": manifest["dataset_id"],
        "feature_version": manifest["feature_version"],
        "spark": {
            "version": spark_version,
            "master": settings.spark_master,
            "shuffle_partitions": settings.spark_shuffle_partitions,
        },
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "processor": platform.processor() or "not reported",
            "logical_cpu_count": os.cpu_count(),
        },
    }
    (root / "benchmark.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report
