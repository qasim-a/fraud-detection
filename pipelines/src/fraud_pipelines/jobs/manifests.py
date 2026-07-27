"""Partitioned Parquet output with reproducible lineage identity."""

import hashlib
import json
from pathlib import Path
from typing import Any

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from fraud_pipelines.features.definitions import FEATURE_VERSION


def write_feature_dataset(
    frame: DataFrame, output: Path, source_manifest: dict[str, Any], partitions: int = 2
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    data_path = output / "data"
    (
        frame.withColumn("event_date", frame.event_time.cast("date"))
        .repartition(partitions, "event_date")
        .write.mode("overwrite")
        .partitionBy("event_date")
        .parquet(str(data_path))
    )
    counts = {"rows": frame.count(), "fraud": frame.where("is_fraud = true").count()}
    row_json = F.to_json(F.struct(*[F.col(name) for name in sorted(frame.columns)]))
    digest_row = (
        frame.select(row_json.alias("row_json"))
        .select(F.sha2("row_json", 256).alias("sha256"), F.xxhash64("row_json").alias("hash64"))
        .agg(F.min("sha256"), F.max("sha256"), F.sum("hash64"), F.count("sha256"))
        .first()
    )
    if digest_row is None:
        raise ValueError("Cannot fingerprint an empty feature dataset")
    content_fingerprint = hashlib.sha256(
        json.dumps([digest_row[0], digest_row[1], digest_row[2], digest_row[3]]).encode()
    ).hexdigest()
    identity_input = {
        "source": source_manifest["dataset_id"],
        "schema": frame.schema.jsonValue(),
        "feature_version": FEATURE_VERSION,
        "counts": counts,
        "partitions": partitions,
        "content_fingerprint": content_fingerprint,
    }
    dataset_id = hashlib.sha256(
        json.dumps(identity_input, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    manifest = {"dataset_id": dataset_id, **identity_input, "output_uri": str(data_path)}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest
