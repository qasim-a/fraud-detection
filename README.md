# Fraud Detection Platform

A full-stack, local-first fraud detection and analyst review platform modeled after the kinds of
systems used by payment processors, brokerages, and banks. It combines distributed historical data
processing, reproducible machine-learning training, low-latency transaction scoring, operational
case management, explainability, and model monitoring in one coherent project.

The platform generates its own deterministic financial data, uses PySpark to turn transaction
history into point-in-time features, trains and evaluates an XGBoost classifier, serves traceable
predictions through FastAPI, persists operational state in PostgreSQL, and presents alerts and
metrics in a React dashboard. No external dataset or private financial data is required.

## What the platform does

The project supports the complete path from raw historical activity to an analyst decision:

1. A deterministic generator creates synthetic accounts, merchants, and chronological transactions.
   It includes normal activity and understandable planted fraud scenarios such as unusually large
   cross-border transactions and rapid transaction velocity.
2. PySpark reads strict schemas, validates transaction quality, quarantines malformed or
   referentially invalid records, joins account and merchant context, and calculates historical
   features using distributed SQL and window operations.
3. The pipeline writes partitioned Parquet data and manifests containing schemas, counts,
   configuration, input lineage, and reproducible dataset fingerprints.
4. Training assigns chronological train, validation, and test periods, compares a logistic
   regression baseline with XGBoost, chooses a threshold on validation data, and reports final
   metrics against the held-out test period.
5. A versioned model artifact is integrity checked, activated, and loaded by the API without placing
   Spark or a JVM in the synchronous request path.
6. FastAPI accepts individual transactions, calculates compatible online features, scores the
   transaction, stores an immutable feature snapshot and prediction, and creates an alert when the
   probability meets the active model threshold.
7. Analysts use the React application to monitor transaction and alert activity, open a
   risk-prioritized queue, inspect transaction context and model influence factors, and record
   append-only review decisions.

## System architecture

```text
                         HISTORICAL / OFFLINE PATH

Synthetic generator
        |
        v
Canonical JSONL snapshots + source hashes
        |
        v
PySpark validation ---------> Quarantined invalid records
        |
        v
Joins + point-in-time window features
        |
        v
Partitioned Parquet + dataset manifest
        |
        v
Chronological split -> Logistic baseline + XGBoost
        |
        v
Model JSON + SHA-256 metadata + model card


                         OPERATIONAL / ONLINE PATH

Transaction request
        |
        v
FastAPI validation -> Online feature transformation -> XGBoost inference
        |                                              |
        |                                              v
        |                                      Risk score + factors
        |                                              |
        v                                              v
PostgreSQL <---- transaction / snapshot / score / alert / review history
        |
        v
FastAPI dashboard and alert APIs
        |
        v
React analyst dashboard
```

Spark owns work that naturally benefits from distributed processing: historical ingestion,
validation, joins, windowed feature engineering, aggregation, and Parquet production. It is
deliberately excluded from synchronous scoring, where a small Python service can load the exported
model directly and respond with low latency.

PostgreSQL and Parquet also have intentionally separate responsibilities. PostgreSQL stores mutable
operational workflow and enforces transactional consistency. Parquet stores immutable analytical
datasets optimized for Spark scans and repeatable model training.

## Analyst experience

The web application contains two primary workspaces.

### Monitoring dashboard

The dashboard presents a consistent UTC time range across:

- Transaction and alert totals
- Amount at risk, without silently mixing in foreign-exchange conversion
- Daily transaction and alert volume
- Low, medium, high, and critical risk-band distribution
- Confirmed fraud, legitimate, needs-review, and explicitly unlabeled outcomes
- Active model identity, dataset identity, feature version, and threshold
- Precision, recall, PR-AUC, confusion counts, and evaluation alert volume

Empty, loading, unavailable, and error states are represented explicitly. Unreviewed alerts are not
silently treated as legitimate transactions when model performance is displayed.

### Alert investigation

The alert queue is ordered by descending risk and supports status, minimum-risk, channel, and
country filtering. Alert detail includes:

- Transaction amount, channel, country, merchant, and model version
- Ranked factors that pushed the prediction higher or lower
- A clear disclaimer that model influence is not proof or cause of fraud
- Workflow status controls
- Confirmed-fraud, legitimate, and needs-review decisions with optional notes
- Complete append-only audit and decision history

Review actions never rewrite the original prediction, probability, threshold, model identity, or
feature snapshot.

## Machine-learning and feature pipeline

### Deterministic synthetic data

The generator uses a configurable seed and stable identifiers. Running the same row count and seed
produces byte-equivalent account, merchant, and transaction snapshots with identical hashes. This
makes the entire project runnable without downloading or committing a large dataset.

### Data quality and feature engineering

Spark applies reusable quality rules for duplicate transaction IDs, invalid amounts or currencies,
and unknown account or merchant references. Invalid records are isolated with reasons while valid
records continue through the pipeline.

Features include time-of-day encodings, prior transaction velocity, trailing account spending
behavior, amount-to-history ratio, country mismatch, and merchant risk. Historical window features
use only records occurring before the transaction being scored. They do not use future reviews,
future activity, or post-event aggregates.

The backend contains a scalar online implementation of the serving-time feature contract. Shared
feature definitions, semantic versions, bounds, defaults, and golden parity fixtures detect drift
between Spark and API transformations.

### Training and evaluation

Training uses chronological rather than random splits. The validation period selects the operating
threshold, and the test period evaluates that fixed threshold. The pipeline reports:

- Precision and recall
- Precision-recall area under the curve
- True-positive, false-positive, true-negative, and false-negative counts
- Alert volume at the selected threshold
- Logistic regression baseline PR-AUC

The XGBoost artifact is saved in JSON format. Its metadata records the artifact SHA-256, dataset ID,
feature version, threshold, evaluation metrics, model version, and timestamps. Training also creates
a human-readable model card describing intended use and limitations.

## Transaction consistency and traceability

Transaction ingestion is idempotent. The client supplies a UUID:

- Repeating the same UUID with the same payload returns the existing result.
- Reusing the UUID with a different payload returns a conflict.
- Validation failures return field-level problem details.
- Model failures persist an explicit `scoring_failed` state with no fabricated probability or alert.

The transaction, feature snapshot, score, and qualifying alert are written atomically. Every score
retains its model version, feature version, threshold, scoring time, and explanation factors. This
allows historical decisions to remain interpretable after a newer model is activated.

## Technically distinctive aspects

This project goes beyond a model notebook or CRUD dashboard in several important ways:

- **Spark has a credible role.** It performs historical validation, joins, window features,
  aggregation, and Parquet output rather than being added to a small request path for appearance.
- **Offline and online features are tested for parity.** Spark stays out of the API while shared
  contracts and golden fixtures make transformation drift detectable.
- **Historical features are point-in-time correct.** Window definitions exclude the current and
  future transactions, reducing a common source of ML leakage.
- **Evaluation respects chronology.** Threshold selection occurs on validation data and final
  metrics use a later test period.
- **Data and model lineage are first-class.** Dataset identities depend on input fingerprints,
  schemas, feature versions, configuration, row counts, and content fingerprints.
- **Model artifacts are verifiable.** The API validates the model's SHA-256 and feature contract
  before serving it.
- **Scoring is operationally honest.** Dependency or model failure becomes a visible terminal state,
  never a default probability disguised as a real prediction.
- **Review history is append-only.** Human outcomes add audit evidence without mutating the original
  model result.
- **Dashboard metrics reconcile to source records.** Totals, risk bands, outcomes, and time buckets
  share the same explicit UTC range contract.
- **Scale claims are evidence-backed.** A benchmark report captures the hardware, software,
  configuration, elapsed time, row counts, output size, and dataset fingerprints.

## Technology stack

| Layer | Technologies | Responsibility |
|---|---|---|
| Historical processing | Python 3.12, PySpark 4.2, Spark SQL | Validation, joins, window features, aggregation, Parquet output |
| Machine learning | XGBoost, scikit-learn, pandas, NumPy | Baseline training, boosted-tree training, chronological evaluation |
| Analytical storage | Parquet, PyArrow, JSON manifests | Immutable features, schemas, lineage, fingerprints, model artifacts |
| API | FastAPI, Pydantic, Uvicorn | Validation, scoring, health, alerts, reviews, dashboard endpoints |
| Persistence | PostgreSQL 17, SQLAlchemy 2, Alembic | Transactions, scores, alerts, model versions, decisions, migrations |
| Frontend | React 19, TypeScript, Vite | Dashboard, alert queue, investigation and review workflow |
| Data fetching and charts | Typed Fetch client, Recharts | API integration, metric cards, accessible operational charts |
| Testing | pytest, Vitest, React Testing Library, Playwright | Unit, contract, integration, parity, Spark, UI, and browser tests |
| Quality | Ruff, Pyright, ESLint, TypeScript | Formatting, linting, and strict static analysis |
| Local operations | Docker Compose, Dockerfiles, Make, uv, pnpm | Reproducible environments and stable developer commands |
| Specification | GitHub Spec Kit | Requirements, architecture, contracts, task sequencing, checklists |

Kafka, Structured Streaming, MLflow, authentication, automated retraining, and cloud deployment are
deliberately outside the current specification. They can be added as later increments without
changing the existing boundary between offline processing and online scoring.

## Repository layout

```text
backend/     FastAPI service, SQLAlchemy models, Alembic migrations, scoring and review logic
pipelines/   Synthetic generation, Spark jobs, training, artifacts, model card, and benchmark
frontend/    React and TypeScript analyst application
infra/       PostgreSQL initialization and service Dockerfiles
tests/       Shared feature fixtures and end-to-end browser journey
specs/       GitHub Spec Kit requirements, plan, contracts, tasks, and acceptance checklists
docs/        Verification, benchmark interpretation, and security audit evidence
artifacts/   Generated data, Parquet, models, manifests, and reports; ignored by Git
```

## Local setup

Prerequisites:

- Docker Desktop or Docker Engine with Compose v2
- Python 3.12 and `uv`
- Java 17 for local Spark execution
- Node.js 22 and pnpm
- `make`
- At least 8 GB memory and 10 GB free disk for the documented demo

Bootstrap and run the complete workflow:

```bash
cp .env.example .env
make bootstrap
docker compose up -d --wait postgres api frontend
make migrate
make generate-demo SEED=20260727 ROWS=50000
make features
make verify-features
make train
make evaluate
make activate-model
make seed-operational-data
make smoke-score
```

Open [http://localhost:5173](http://localhost:5173). PostgreSQL is exposed on host port 5433 by
default to avoid collisions with a locally installed database. Generated data and models remain
under `artifacts/` and are not committed.

To stop the application while preserving generated artifacts and the PostgreSQL named volume:

```bash
docker compose down
```

## Verification and measured results

```bash
make check
make test-integration
make test-e2e
make benchmark ROWS=1000000 SEED=20260727
```

The verified suite includes backend and pipeline unit tests, OpenAPI contract tests, database and
Spark integration tests, offline/online feature parity, frontend behavior tests, keyboard and chart
accessibility checks, and a Playwright analyst journey.

The documented local benchmark processed 1,000,000 synthetic transactions with zero rejected rows
in 64.383 seconds on an 8-logical-CPU ARM Mac, producing 207,852,529 bytes of Parquet output. This is
evidence for that recorded local environment, not a general production-throughput claim.

During the verified local scoring workload, 100 out of 100 idempotent requests completed in under
two seconds; the maximum observed request time was 0.024863 seconds. Full command output, dataset
identities, failure checks, and environment details are in
[docs/verification.md](docs/verification.md). Benchmark interpretation guidance is in
[docs/benchmarking.md](docs/benchmarking.md).

## API behavior

The versioned API exposes health, transaction ingestion and retrieval, alert queue and detail,
review status and decision operations, dashboard summaries, and active-model metadata. The formal
contract is maintained in
[`specs/001-fraud-review-platform/contracts/openapi.yaml`](specs/001-fraud-review-platform/contracts/openapi.yaml).

Errors use structured problem responses with an HTTP status, human-readable detail, and field-level
validation errors where applicable. Logs use structured JSON and redact configured sensitive keys.

## Security and data policy

Only deterministic synthetic or public anonymized data is permitted. Real payment instruments,
credentials, customer identities, bank-account numbers, or identifying financial records must not
enter source control, generated fixtures, or logs. Environment secrets and generated artifacts are
ignored by Git, database access uses SQLAlchemy-bound values, and pipeline failures avoid serializing
input records.

The source and history audit is documented in [docs/security-audit.md](docs/security-audit.md).

## Limitations

- Synthetic fraud patterns are intentionally understandable and substantially simpler than real
  adaptive fraud behavior.
- Reported metrics do not establish real-world accuracy, calibration, fairness, regulatory
  compliance, or business value.
- The platform has one demo analyst role and no authentication or multi-tenant access control.
- It does not move, block, approve, reverse, or otherwise control real funds.
- Scores prioritize human review; they must not be interpreted as autonomous accusations.
- Amount-at-risk totals do not perform foreign-exchange conversion.
- Kafka streaming, model drift detection, automated retraining, and production deployment require
  separate operational and model-risk specifications.

## Troubleshooting

- **Docker is unavailable:** start Docker Desktop or Docker Engine and wait until `docker info`
  succeeds.
- **API reports the model unavailable:** run `make train` and `make activate-model`. Restart the API
  if it was started before an artifact existed.
- **Spark does not launch:** confirm Python 3.12 and Java 17. Reduce the input row count or Spark
  shuffle partitions on constrained hardware.
- **A port is occupied:** change `POSTGRES_PORT`, `API_PORT`, or `FRONTEND_PORT` in the ignored `.env`
  file. Defaults are 5433, 8000, and 5173.
- **Playwright has no browser binary:** run
  `pnpm --dir frontend exec playwright install chromium`.
- **The dashboard is empty:** seed operational data and submit transactions with
  `make seed-operational-data` and `make smoke-score`. Historical Parquet generation does not copy
  all batch transactions into PostgreSQL by design.
