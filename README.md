# Fraud Detection Platform

A local-first, Spark-powered fraud review platform that turns deterministic synthetic transaction
history into point-in-time features and an XGBoost model, serves traceable fraud scores through
FastAPI, and gives analysts a React dashboard for investigation and monitoring.

No external dataset is required. The generator plants understandable fraud scenarios, and every
dataset, feature set, model, threshold, score, alert, and review decision retains versioned lineage.

## Architecture

```text
Synthetic generator -> JSONL + manifest -> PySpark validation/features -> Parquet + manifest
                                                                  |
                                                                  v
                                                      XGBoost artifact + model card
                                                                  |
Transaction request -> FastAPI scoring -> PostgreSQL -> alerts/reviews/metrics -> React dashboard
```

Spark owns historical validation, joins, window features, and Parquet production. It is
deliberately absent from the synchronous API path. PostgreSQL stores mutable operational workflow;
Parquet and JSON manifests store immutable analytical outputs.

## Capabilities

- Idempotent transaction ingestion with strict validation and explicit scoring failures
- Versioned fraud probabilities, risk bands, thresholds, and per-score influence factors
- Risk-prioritized alert queue with append-only decisions and audit history
- Reconciled dashboard totals, time series, risk bands, outcomes, and model metrics
- Deterministic data generation, Spark quality quarantine, point-in-time features, chronological
  training/evaluation, artifact integrity checks, and model-card generation
- Repeatable million-row benchmark with environment and lineage capture

## Repository layout

```text
backend/     FastAPI scoring and analyst-review service
pipelines/   PySpark generation, feature engineering, training, and benchmarking
frontend/    React and TypeScript analyst dashboard
infra/       Container and PostgreSQL support
tests/       Shared fixtures and Playwright analyst journey
docs/        Benchmark, verification, and security evidence
artifacts/   Generated data and models (ignored by Git)
```

## Quick start

Prerequisites are Docker Desktop or Docker Engine with Compose v2, `make`, `uv`, Node.js 22,
pnpm, and at least 8 GB memory and 10 GB free disk. Local pipeline execution also needs Python 3.12
and Java 17.

```bash
cp .env.example .env
make bootstrap
docker compose up --build -d postgres api frontend
make migrate
make generate-demo SEED=20260727 ROWS=50000
make features
make train
make evaluate
make activate-model
make seed-operational-data
make smoke-score
```

Open `http://localhost:5173`. The complete expected workflow and failure checks are in the
[quickstart validation guide](specs/001-fraud-review-platform/quickstart.md).

## Verification

```bash
make check
make test-integration
make test-e2e
make benchmark ROWS=1000000 SEED=20260727
```

`make check` covers linting, strict Python type analysis, unit and API-contract tests, the frontend
build, and Compose validation. Integration tests require local Spark and PostgreSQL/Docker as
documented. Benchmark reports are described in [docs/benchmarking.md](docs/benchmarking.md).

## Model card and explainability

Training exports `model.json`, integrity-checked `metadata.json`, and `MODEL_CARD.md`. The metadata
records the dataset and feature versions, threshold, precision, recall, PR-AUC, confusion counts,
and alert volume. Score factors indicate whether a feature pushed this model's prediction higher or
lower; they do not prove a cause or establish that fraud occurred.

## Limitations

- The data and planted fraud patterns are synthetic and simpler than real adversarial behavior.
- Reported metrics do not establish real-world accuracy, fairness, calibration, or business value.
- This demonstration has one analyst role and one active model; it is not a production authorization
  system and must not autonomously decline transactions or accuse a person of fraud.
- Kafka, streaming, Redis, MLflow, retraining automation, authentication, and cloud deployment are
  intentionally outside the current specification.
- The local benchmark is evidence for one recorded environment, not a general throughput claim.

## Troubleshooting

- `Cannot connect to the Docker daemon`: start Docker Desktop/Engine and wait until
  `docker info` succeeds.
- API health reports the model unavailable: run `make train` and `make activate-model`, then restart
  the API container if its mounted artifact has not refreshed.
- Spark fails to launch: confirm Java 17 with `java -version` and Python 3.12 with
  `python --version`; reduce `SPARK_SHUFFLE_PARTITIONS` or the row count on constrained machines.
- Port 5432, 8000, or 5173 is occupied: change the matching value in the ignored `.env` file.
- Browser binaries are absent: run `pnpm --dir frontend exec playwright install chromium`.

## Data and security policy

Only public anonymized or deterministic synthetic data is permitted. Never add real payment
credentials, customer records, account numbers, identifying financial information, secrets, or
generated artifacts. See [docs/security-audit.md](docs/security-audit.md) for the current audit.
