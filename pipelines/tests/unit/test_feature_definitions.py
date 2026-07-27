import json
from pathlib import Path

from fraud_pipelines.features.definitions import FEATURE_VERSION, FEATURES


def test_spark_feature_contract_matches_golden_fixture() -> None:
    fixture = json.loads(Path("tests/fixtures/feature_parity.json").read_text())

    assert fixture["feature_version"] == FEATURE_VERSION
    assert list(fixture["cases"][0]["expected"]) == [feature.name for feature in FEATURES]
