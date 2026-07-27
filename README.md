# Fraud Detection Platform

A Spark-first portfolio platform for reproducible transaction feature engineering, fraud scoring,
analyst review, model explainability, and operational monitoring.

The project is currently under implementation. Product requirements, architecture, API contracts,
and the dependency-ordered backlog are in
[`specs/001-fraud-review-platform`](specs/001-fraud-review-platform/).

## Repository layout

```text
backend/     FastAPI scoring and analyst-review service
pipelines/   PySpark data generation, feature engineering, and model training
frontend/    React and TypeScript analyst dashboard
infra/       Container and PostgreSQL support files
tests/       Cross-service and browser-level fixtures and tests
artifacts/   Generated data and model files (ignored by Git)
```

## Planned local workflow

```bash
cp .env.example .env
make bootstrap
make check
```

Local prerequisites are Python 3.12, Java 17, Node.js 22, pnpm, Docker Compose v2, `uv`, and `make`.

See the [quickstart validation guide](specs/001-fraud-review-platform/quickstart.md) for the target
end-to-end workflow. Commands will become operational as their corresponding implementation phases
are completed.

## Data policy

Only public anonymized or deterministic synthetic data is permitted. Do not add real payment
credentials, customer records, account numbers, or identifying financial information.
