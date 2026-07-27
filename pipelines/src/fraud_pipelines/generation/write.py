"""Canonical JSONL snapshots and fingerprinted bronze manifests."""

import hashlib
import json
from pathlib import Path
from typing import Any

from fraud_pipelines.schemas.raw import SCHEMA_VERSION


def canonical_bytes(rows: list[dict[str, object]]) -> bytes:
    return b"".join(
        (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode() for row in rows
    )


def write_snapshot(
    root: Path, seed: int, datasets: dict[str, list[dict[str, object]]]
) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    files: dict[str, dict[str, object]] = {}
    for name, rows in sorted(datasets.items()):
        payload = canonical_bytes(rows)
        path = root / f"{name}.jsonl"
        path.write_bytes(payload)
        files[name] = {
            "path": str(path),
            "rows": len(rows),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    identity_material = {
        name: {"rows": details["rows"], "sha256": details["sha256"]}
        for name, details in files.items()
    }
    identity = hashlib.sha256(json.dumps(identity_material, sort_keys=True).encode()).hexdigest()
    manifest = {
        "dataset_id": identity,
        "schema_version": SCHEMA_VERSION,
        "seed": seed,
        "files": files,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest
