from pathlib import Path
from typing import Any, cast

import yaml
from fraud_api.main import app
from openapi_spec_validator import validate


def load_contract() -> dict[str, Any]:
    path = Path("specs/001-fraud-review-platform/contracts/openapi.yaml")
    contract = cast(object, yaml.safe_load(path.read_text()))
    assert isinstance(contract, dict)
    return cast(dict[str, Any], contract)


def test_committed_openapi_contract_is_valid() -> None:
    validate(load_contract())


def test_generated_health_schema_matches_committed_contract() -> None:
    contract = load_contract()
    generated = app.openapi()

    assert "/health" in contract["paths"]
    assert "/api/v1/health" in generated["paths"]
    assert generated["components"]["schemas"]["HealthResponse"]["required"] == [
        "status",
        "database",
        "model",
    ]
