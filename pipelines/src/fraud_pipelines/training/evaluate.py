# pyright: basic
"""Class-imbalance-aware evaluation and threshold trade-offs."""

from typing import Any

import numpy as np
from sklearn.metrics import average_precision_score, confusion_matrix, precision_recall_curve


def evaluate_probabilities(
    labels: np.ndarray,
    probabilities: np.ndarray,
    minimum_precision: float = 0.7,
    threshold: float | None = None,
) -> dict[str, Any]:
    if len(np.unique(labels)) < 2:
        raise ValueError("Evaluation requires both fraud and legitimate labels")
    if threshold is None:
        precision_curve, recall_curve, thresholds = precision_recall_curve(labels, probabilities)
        candidates = [
            (float(thresholds[i]), float(precision_curve[i]), float(recall_curve[i]))
            for i in range(len(thresholds))
            if precision_curve[i] >= minimum_precision
        ]
        threshold = max(candidates, key=lambda item: item[2])[0] if candidates else 0.5
    predicted = probabilities >= threshold
    tn, fp, fn, tp = confusion_matrix(labels, predicted, labels=[0, 1]).ravel()
    precision = float(tp / (tp + fp)) if tp + fp else 0.0
    recall = float(tp / (tp + fn)) if tp + fn else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "pr_auc": float(average_precision_score(labels, probabilities)),
        "true_positive": int(tp),
        "false_positive": int(fp),
        "true_negative": int(tn),
        "false_negative": int(fn),
        "alert_volume": int(predicted.sum()),
        "threshold": threshold,
    }
