"""Integrity-checked XGBoost JSON artifacts and serving metadata."""

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from xgboost import XGBClassifier

from fraud_pipelines.features.definitions import FEATURE_VERSION


def export_artifact(
    model: XGBClassifier, output: Path, dataset_id: str, metrics: dict[str, Any]
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    artifact = output / "model.json"
    model.get_booster().save_model(artifact)
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    now = datetime.now(UTC).isoformat()
    version = f"fraud-xgb-{dataset_id[:12]}"
    metadata = {
        "name": "fraud-xgboost",
        "version": version,
        "feature_version": FEATURE_VERSION,
        "dataset_id": dataset_id,
        "artifact_sha256": digest,
        "threshold": metrics["threshold"],
        "metrics": {key: value for key, value in metrics.items() if key != "threshold"},
        "created_at": now,
        "activated_at": now,
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    return metadata


def activate_artifact(candidate: Path, active: Path) -> None:
    metadata = json.loads((candidate / "metadata.json").read_text())
    artifact = candidate / "model.json"
    if hashlib.sha256(artifact.read_bytes()).hexdigest() != metadata["artifact_sha256"]:
        raise ValueError("Candidate artifact integrity check failed")
    active.mkdir(parents=True, exist_ok=True)
    shutil.copy2(artifact, active / "model.json")
    shutil.copy2(candidate / "metadata.json", active / "metadata.json")
