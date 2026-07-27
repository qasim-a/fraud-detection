import hashlib
import json
from datetime import UTC, datetime

import pytest
from fraud_api.core.config import Settings
from fraud_api.features.definitions import FEATURE_VERSION
from fraud_api.models.loader import ModelUnavailableError, load_model_bundle


def _settings(tmp_path):
    return Settings(
        model_artifact_path=tmp_path / "model.ubj",
        model_metadata_path=tmp_path / "metadata.json",
    )


def _write_metadata(settings: Settings, artifact_sha256: str) -> None:
    timestamp = datetime(2026, 7, 27, tzinfo=UTC).isoformat()
    settings.model_metadata_path.write_text(
        json.dumps(
            {
                "name": "fraud-xgboost",
                "version": "test-v1",
                "feature_version": FEATURE_VERSION,
                "dataset_id": "test-dataset",
                "artifact_sha256": artifact_sha256,
                "threshold": 0.7,
                "metrics": {"average_precision": 0.8},
                "created_at": timestamp,
                "activated_at": timestamp,
            }
        )
    )


def test_loader_rejects_missing_artifact(tmp_path):
    with pytest.raises(ModelUnavailableError, match="missing"):
        load_model_bundle(_settings(tmp_path))


def test_loader_rejects_artifact_hash_mismatch(tmp_path):
    settings = _settings(tmp_path)
    settings.model_artifact_path.write_bytes(b"not-a-model")
    _write_metadata(settings, "0" * 64)

    with pytest.raises(ModelUnavailableError, match="integrity"):
        load_model_bundle(settings)


def test_loader_rejects_unreadable_xgboost_artifact(tmp_path):
    settings = _settings(tmp_path)
    artifact = b"not-a-model"
    settings.model_artifact_path.write_bytes(artifact)
    _write_metadata(settings, hashlib.sha256(artifact).hexdigest())

    with pytest.raises(ModelUnavailableError, match="cannot be loaded"):
        load_model_bundle(settings)
