"""Temporary application entry point completed during the foundation phase."""

from fastapi import FastAPI

app = FastAPI(title="Fraud Review API", version="0.1.0")


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    """Return setup-phase process health without claiming dependency readiness."""
    return {"status": "setup", "database": "unconfigured", "model": "unavailable"}
