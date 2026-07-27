import hashlib

import numpy as np
import pandas as pd
from fraud_pipelines.features.definitions import FEATURES
from fraud_pipelines.training.artifacts import activate_artifact, export_artifact
from fraud_pipelines.training.evaluate import evaluate_probabilities
from fraud_pipelines.training.splits import chronological_split
from fraud_pipelines.training.train import train_models


def test_chronological_training_metrics_and_artifact(tmp_path) -> None:
    rng = np.random.default_rng(42)
    rows = 240
    frame = pd.DataFrame({feature.name: rng.random(rows) for feature in FEATURES})
    frame["id"] = [f"t-{index:04d}" for index in range(rows)]
    frame["event_time"] = pd.date_range("2025-01-01", periods=rows, freq="h")
    frame["is_fraud"] = np.array([index % 7 == 0 for index in range(rows)])
    split = chronological_split(frame)
    assert (
        split[split.split == "train"].event_time.max()
        < split[split.split == "validation"].event_time.min()
    )
    result = train_models(split, 42)
    test = split[split.split == "test"]
    metrics = evaluate_probabilities(
        test.is_fraud.to_numpy(), result.test_probabilities, minimum_precision=0.1
    )
    required = {
        "precision",
        "recall",
        "pr_auc",
        "true_positive",
        "false_positive",
        "true_negative",
        "false_negative",
        "alert_volume",
        "threshold",
    }
    assert required <= metrics.keys()
    candidate, active = tmp_path / "candidate", tmp_path / "active"
    metadata = export_artifact(result.model, candidate, "dataset-123", metrics)
    activate_artifact(candidate, active)
    assert (
        metadata["artifact_sha256"]
        == hashlib.sha256((active / "model.json").read_bytes()).hexdigest()
    )
