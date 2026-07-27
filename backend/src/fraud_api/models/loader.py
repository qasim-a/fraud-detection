"""Integrity-checked XGBoost artifact loading."""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

import numpy as np
import xgboost as xgb
from pydantic import BaseModel, ConfigDict, Field

from fraud_api.core.config import Settings
from fraud_api.features.definitions import FEATURE_VERSION, FEATURES


class ModelUnavailableError(RuntimeError):
    """Raised when the configured model cannot be safely loaded."""


class ModelMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    feature_version: str
    dataset_id: str
    artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    threshold: float = Field(ge=0, le=1)
    metrics: dict[str, float | int]
    created_at: datetime
    activated_at: datetime


class Predictor(Protocol):
    def predict_probability(self, features: dict[str, float | int]) -> float: ...

    def predict_contributions(self, features: dict[str, float | int]) -> list[float]: ...


class XGBoostPredictor:
    def __init__(self, booster: xgb.Booster) -> None:
        self._booster = booster
        self._names = [feature.name for feature in FEATURES]

    def _matrix(self, features: dict[str, float | int]) -> xgb.DMatrix:
        row = np.asarray([[features[name] for name in self._names]], dtype=np.float32)
        return xgb.DMatrix(row, feature_names=self._names)

    def predict_probability(self, features: dict[str, float | int]) -> float:
        return float(self._booster.predict(self._matrix(features))[0])

    def predict_contributions(self, features: dict[str, float | int]) -> list[float]:
        values = self._booster.predict(self._matrix(features), pred_contribs=True)[0]
        return [float(value) for value in values[:-1]]


@dataclass(frozen=True, slots=True)
class ModelBundle:
    metadata: ModelMetadata
    predictor: Predictor
    artifact_path: Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_model_bundle(settings: Settings) -> ModelBundle:
    artifact_path = settings.model_artifact_path
    metadata_path = settings.model_metadata_path
    if not artifact_path.is_file() or not metadata_path.is_file():
        raise ModelUnavailableError("Configured model artifact or metadata is missing")
    try:
        metadata = ModelMetadata.model_validate_json(metadata_path.read_text())
    except (OSError, ValueError) as exc:
        raise ModelUnavailableError("Model metadata is invalid") from exc
    if metadata.feature_version != FEATURE_VERSION:
        raise ModelUnavailableError("Model feature version is incompatible")
    if sha256_file(artifact_path) != metadata.artifact_sha256:
        raise ModelUnavailableError("Model artifact integrity check failed")
    try:
        booster = xgb.Booster()
        booster.load_model(str(artifact_path))  # pyright: ignore[reportUnknownMemberType]
    except xgb.core.XGBoostError as exc:
        raise ModelUnavailableError("Model artifact cannot be loaded") from exc
    return ModelBundle(
        metadata=metadata, predictor=XGBoostPredictor(booster), artifact_path=artifact_path
    )
