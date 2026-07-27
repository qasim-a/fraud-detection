# Implementation Plan: Fraud Review Platform

**Branch**: `main` | **Date**: 2026-07-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-fraud-review-platform/spec.md`

## Summary

Deliver a local-first fraud review platform as incremental vertical slices. A deterministic
generator creates synthetic accounts, merchants, and transactions. PySpark validates and joins
historical inputs, builds point-in-time features, and writes versioned Parquet datasets. XGBoost is
trained with chronological evaluation and exported as a versioned artifact. FastAPI performs
low-latency scoring with compatible online transformations, persists transactions, predictions,
alerts, and reviews in PostgreSQL, and serves a React analyst dashboard. Kafka and Structured
Streaming remain outside the MVP and require a later specification.

## Technical Context

**Language/Version**: Python 3.12 for backend, ML, generator, and pipelines; Java 17 for Spark;
TypeScript 5.x for the web application

**Primary Dependencies**: PySpark 4.2.x, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, XGBoost 3.x,
scikit-learn, SHAP, pandas, PyArrow, React 19, Vite, TanStack Query, Recharts

**Storage**: PostgreSQL 17+ for operational records; Parquet on a mounted local object-store-style
directory for analytical datasets; versioned JSON model artifacts and metadata on the same volume

**Testing**: pytest with unit, contract, and integration markers; testcontainers or Docker Compose
for PostgreSQL integration; local Spark sessions for pipeline tests; Vitest and React Testing
Library for frontend behavior; Playwright for one end-to-end analyst journey

**Target Platform**: Linux containers via Docker Compose; local development on macOS or Linux,
including ARM64; modern Chromium, Firefox, and Safari-class browsers

**Project Type**: Web application plus batch data and ML pipelines in a monorepo

**Performance Goals**: Individual scoring under 2 seconds for at least 99% of requests in the local
demo workload; dashboard summary queries under 2 seconds for the seeded demo; repeatable processing
of at least one million synthetic transactions with documented elapsed time

**Constraints**: Spark stays outside the synchronous HTTP path; no real financial or personal data;
all predictions retain model and feature versions; 2 GB quick-demo dataset target and an adjustable
larger benchmark; service startup and verification use documented commands

**Scale/Scope**: One organization and analyst role; tens of thousands of operational demo records;
one million or more analytical records; one active model with retained historical versions; four
user journeys from ingestion through batch feature production

## Constitution Check

*GATE: Passed before research and re-checked after design on 2026-07-27.*

- **Spark role — PASS**: Spark owns historical validation, joins, point-in-time feature engineering,
  aggregation, and Parquet output. FastAPI owns synchronous scoring.
- **ML integrity — PASS**: Dataset fingerprints, chronological splits, feature/model versions,
  class-imbalance metrics, threshold metadata, and non-causal explanation language are designed.
- **Safety — PASS**: Only deterministic synthetic data is required. Secrets use environment files;
  payloads and logs exclude payment credentials and identifying financial data.
- **Contracts and observability — PASS**: OpenAPI, relational entities, model metadata, processing-run
  lineage, idempotency, structured logging, and boundary tests are explicit.
- **Incremental quality — PASS**: The plan starts with a batch-scored vertical slice. Kafka, Redis,
  MLflow, streaming, drift monitoring, and retraining remain deferred.

## Project Structure

### Documentation (this feature)

```text
specs/001-fraud-review-platform/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml
├── src/fraud_api/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   └── services/
└── tests/
    ├── contract/
    ├── integration/
    └── unit/

pipelines/
├── pyproject.toml
├── src/fraud_pipelines/
│   ├── features/
│   ├── generation/
│   ├── jobs/
│   ├── schemas/
│   └── training/
└── tests/
    ├── integration/
    └── unit/

frontend/
├── package.json
├── src/
│   ├── api/
│   ├── components/
│   ├── features/
│   ├── pages/
│   └── routes/
└── tests/

infra/
├── docker/
└── postgres/

artifacts/                 # ignored generated data and model artifacts
├── bronze/
├── silver/
├── features/
└── models/

tests/
└── e2e/

compose.yaml
Makefile
.env.example
```

**Structure Decision**: A monorepo separates low-latency application code, distributed batch/ML
code, and browser code while keeping their schemas and end-to-end verification versioned together.
The backend and pipelines use independent Python packages so the API image does not include Spark or
Java. Generated artifacts remain outside Git.

## Design Decisions

### Processing and serving boundary

PySpark reads deterministic raw snapshots, validates schemas, quarantines invalid rows, joins
accounts and merchants, computes point-in-time aggregates with DataFrame/window operations, and
writes partitioned Parquet plus a manifest. Training consumes only a completed manifest. The API
loads the approved model and a small shared feature-definition package, then computes request-time
features from transaction context and precomputed account summaries stored operationally. No Spark
session is created by an API worker.

### Incremental delivery sequence

1. Repository/tooling foundation and deterministic synthetic generator.
2. Spark bronze-to-feature pipeline with lineage and reproducibility tests.
3. Chronological XGBoost training, evaluation, threshold selection, and versioned artifact export.
4. Transaction scoring API with PostgreSQL persistence, idempotency, alerts, and explanations.
5. Analyst alert queue, detail/review workflow, reconciled charts, and end-to-end validation.

### Model threshold and explanations

Training records a precision-recall curve and selects a configurable demonstration threshold using
a minimum precision target plus alert-volume reporting. It never presents the selected threshold as
universally optimal. Tree contribution values are calculated for the scored row, grouped into
human-readable factors, and stored with the prediction. The UI labels them as factors that pushed
the score higher or lower.

## Complexity Tracking

No constitution violations require justification.
