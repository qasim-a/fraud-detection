# pyright: basic
"""Reproducible synthetic-data, Spark feature, and model pipeline CLI."""

import json

import typer
from pyspark.sql import SparkSession

from fraud_pipelines.config import get_pipeline_settings
from fraud_pipelines.generation.entities import generate_accounts, generate_merchants
from fraud_pipelines.generation.transactions import generate_transactions
from fraud_pipelines.generation.write import write_snapshot
from fraud_pipelines.jobs.features import build_features
from fraud_pipelines.jobs.manifests import write_feature_dataset
from fraud_pipelines.jobs.run import execute_run
from fraud_pipelines.jobs.validation import validate_transactions
from fraud_pipelines.schemas.raw import ACCOUNT_SCHEMA, MERCHANT_SCHEMA, TRANSACTION_SCHEMA
from fraud_pipelines.training.artifacts import activate_artifact, export_artifact
from fraud_pipelines.training.evaluate import evaluate_probabilities
from fraud_pipelines.training.splits import chronological_split
from fraud_pipelines.training.train import train_models

app = typer.Typer(no_args_is_help=True)


def _spark() -> SparkSession:
    settings = get_pipeline_settings()
    return (
        SparkSession.builder.master(settings.spark_master)
        .appName("fraud-pipelines")
        .config("spark.sql.shuffle.partitions", str(settings.spark_shuffle_partitions))
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )


@app.command()
def version() -> None:
    typer.echo("0.1.0")


@app.command("show-config")
def show_config() -> None:
    typer.echo(get_pipeline_settings().model_dump_json())


@app.command()
def generate(seed: int = 20260727, rows: int = 50_000) -> None:
    settings = get_pipeline_settings()
    account_count = max(100, rows // 20)
    merchant_count = max(25, rows // 200)
    accounts = generate_accounts(seed, account_count)
    merchants = generate_merchants(seed, merchant_count)
    transactions = generate_transactions(seed, rows, accounts, merchants)
    manifest = write_snapshot(
        settings.bronze_root,
        seed,
        {"accounts": accounts, "merchants": merchants, "transactions": transactions},
    )
    typer.echo(json.dumps({"dataset_id": manifest["dataset_id"], "rows": rows}))


@app.command()
def features() -> None:
    settings = get_pipeline_settings()
    source = json.loads((settings.bronze_root / "manifest.json").read_text())
    spark = _spark()
    try:
        accounts = spark.read.schema(ACCOUNT_SCHEMA).json(
            str(settings.bronze_root / "accounts.jsonl")
        )
        merchants = spark.read.schema(MERCHANT_SCHEMA).json(
            str(settings.bronze_root / "merchants.jsonl")
        )
        transactions = spark.read.schema(TRANSACTION_SCHEMA).json(
            str(settings.bronze_root / "transactions.jsonl")
        )
        result = validate_transactions(transactions, accounts, merchants)
        quarantine = settings.feature_root / "quarantine"
        result.quarantine.write.mode("overwrite").parquet(str(quarantine))
        manifest = execute_run(
            "features",
            settings.feature_root,
            {
                "source": source["dataset_id"],
                "input_uris": [details["path"] for details in source["files"].values()],
                "input_fingerprints": {
                    name: details["sha256"] for name, details in source["files"].items()
                },
                "schema_version": source["schema_version"],
            },
            lambda: {
                **write_feature_dataset(
                    build_features(result.valid, accounts, merchants), settings.feature_root, source
                ),
                "processed_count": result.valid.count(),
                "rejected_count": result.quarantine.count(),
            },
        )
        typer.echo(
            json.dumps({"dataset_id": manifest["dataset_id"], "rows": manifest["processed_count"]})
        )
    finally:
        spark.stop()


def _training_frame():
    settings = get_pipeline_settings()
    spark = _spark()
    try:
        frame = spark.read.parquet(str(settings.feature_root / "data")).toPandas()
    finally:
        spark.stop()
    frame["event_time"] = frame["event_time"].astype("datetime64[ns]")
    return chronological_split(frame)


@app.command()
def train(seed: int = 20260727) -> None:
    settings = get_pipeline_settings()
    feature_manifest = json.loads((settings.feature_root / "manifest.json").read_text())
    frame = _training_frame()
    result = train_models(frame, seed)
    validation = frame[frame.split == "validation"]
    test = frame[frame.split == "test"]
    selection = evaluate_probabilities(
        validation.is_fraud.to_numpy(), result.validation_probabilities
    )
    metrics = evaluate_probabilities(
        test.is_fraud.to_numpy(), result.test_probabilities, threshold=selection["threshold"]
    )
    metrics["baseline_pr_auc"] = result.baseline_pr_auc
    candidate = settings.model_root / "candidate"
    metadata = export_artifact(result.model, candidate, feature_manifest["dataset_id"], metrics)
    typer.echo(json.dumps({"version": metadata["version"], "metrics": metadata["metrics"]}))


@app.command()
def evaluate() -> None:
    metadata = json.loads(
        (get_pipeline_settings().model_root / "candidate" / "metadata.json").read_text()
    )
    typer.echo(
        json.dumps(
            {
                "version": metadata["version"],
                "threshold": metadata["threshold"],
                "metrics": metadata["metrics"],
            }
        )
    )


@app.command("activate-model")
def activate_model() -> None:
    root = get_pipeline_settings().model_root
    activate_artifact(root / "candidate", root / "active")
    typer.echo("active")
