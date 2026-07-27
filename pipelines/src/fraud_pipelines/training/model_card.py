"""Human-readable documentation for a versioned fraud model artifact."""

from pathlib import Path
from typing import Any


def render_model_card(metadata: dict[str, Any]) -> str:
    metrics = metadata["metrics"]
    return f"""# Model Card: {metadata["version"]}

## Model and data

- Model: XGBoost binary classifier
- Dataset ID: `{metadata["dataset_id"]}`
- Feature contract: `{metadata["feature_version"]}`
- Decision threshold: `{metadata["threshold"]:.6f}`
- Artifact SHA-256: `{metadata["artifact_sha256"]}`

## Chronological test metrics

- Precision: {metrics["precision"]:.4f}
- Recall: {metrics["recall"]:.4f}
- PR-AUC: {metrics["pr_auc"]:.4f}
- Alert volume: {metrics["alert_volume"]}
- Confusion counts: TP {metrics["true_positive"]}, FP {metrics["false_positive"]},
  TN {metrics["true_negative"]}, FN {metrics["false_negative"]}

## Intended use

This synthetic-data demonstration prioritizes transactions for human review. It does not authorize
declines, accuse people of fraud, or represent production-calibrated financial risk.

## Limitations

Metrics describe one deterministic synthetic dataset and do not establish performance on real
payments. Planted fraud scenarios are simpler than adversarial behavior, probability calibration
has not been validated, and feature coverage is intentionally small. Per-score factors describe
model influence, not causation. Human review and domain validation remain mandatory.
"""


def write_model_card(path: Path, metadata: dict[str, Any]) -> None:
    path.write_text(render_model_card(metadata))
