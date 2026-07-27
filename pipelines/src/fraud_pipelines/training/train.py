# pyright: basic
"""Logistic baseline and early-stopped XGBoost training."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from xgboost import XGBClassifier

from fraud_pipelines.features.definitions import FEATURES


@dataclass(frozen=True, slots=True)
class TrainingResult:
    model: XGBClassifier
    baseline_pr_auc: float
    validation_probabilities: np.ndarray
    test_probabilities: np.ndarray


def train_models(frame: pd.DataFrame, seed: int) -> TrainingResult:
    names = [feature.name for feature in FEATURES]
    train, validation, test = (
        frame[frame.split == name] for name in ("train", "validation", "test")
    )
    if min(len(train), len(validation), len(test)) == 0:
        raise ValueError("Chronological train, validation, and test splits must be non-empty")
    weight = max(1.0, float((train.is_fraud == 0).sum()) / max(1, int((train.is_fraud == 1).sum())))
    baseline = LogisticRegression(max_iter=500, class_weight="balanced", random_state=seed)
    baseline.fit(train[names], train.is_fraud)
    baseline_auc = float(
        average_precision_score(
            validation.is_fraud, baseline.predict_proba(validation[names])[:, 1]
        )
    )
    model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="aucpr",
        random_state=seed,
        scale_pos_weight=weight,
        early_stopping_rounds=20,
        n_jobs=2,
    )
    model.fit(
        train[names],
        train.is_fraud,
        eval_set=[(validation[names], validation.is_fraud)],
        verbose=False,
    )
    return TrainingResult(
        model=model,
        baseline_pr_auc=baseline_auc,
        validation_probabilities=model.predict_proba(validation[names])[:, 1],
        test_probabilities=model.predict_proba(test[names])[:, 1],
    )
