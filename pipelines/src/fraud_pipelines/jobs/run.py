"""Sanitized processing-run manifests."""

import json
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def execute_run(
    job_name: str,
    output: Path,
    configuration: dict[str, Any],
    operation: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    started = datetime.now(UTC)
    run: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "job_name": job_name,
        "job_version": "1.0.0",
        "status": "running",
        "configuration": configuration,
        "input_uris": configuration.get("input_uris", []),
        "input_fingerprints": configuration.get("input_fingerprints", {}),
        "schema_version": configuration.get("schema_version"),
        "started_at": started.isoformat(),
    }
    try:
        result = operation()
        run.update(result, status="succeeded", completed_at=datetime.now(UTC).isoformat())
    except Exception as exc:
        run.update(
            status="failed",
            completed_at=datetime.now(UTC).isoformat(),
            error_summary=type(exc).__name__,
        )
        raise
    finally:
        output.mkdir(parents=True, exist_ok=True)
        (output / "run.json").write_text(json.dumps(run, indent=2, sort_keys=True) + "\n")
    return run
