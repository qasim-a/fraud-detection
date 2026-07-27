from pathlib import Path

from fraud_pipelines.config import PipelineSettings


def test_artifact_directories_derive_from_root() -> None:
    settings = PipelineSettings(artifact_root=Path("generated"), generator_seed=7)

    assert settings.bronze_root == Path("generated/bronze")
    assert settings.feature_root == Path("generated/features")
    assert settings.model_root == Path("generated/models")
    assert settings.generator_seed == 7
