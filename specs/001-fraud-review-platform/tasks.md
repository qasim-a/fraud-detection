# Tasks: Fraud Review Platform

**Input**: Design documents from `specs/001-fraud-review-platform/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/openapi.yaml`,
`quickstart.md`

**Tests**: Automated tests are required by the project constitution. Contract and integration tests
must precede implementation at service boundaries.

**Format**: `[ID] [P?] [Story?] Description with exact file path`

## Phase 1: Setup

**Purpose**: Create reproducible package, frontend, container, and developer-tool foundations.

- [X] T001 Create the monorepo directories and root project overview in `README.md`
- [X] T002 Configure ignored secrets, generated artifacts, caches, and local environments in `.gitignore`
- [X] T003 Add documented non-secret runtime configuration defaults in `.env.example`
- [X] T004 [P] Initialize the API package and dependency groups in `backend/pyproject.toml`
- [X] T005 [P] Initialize the Spark and ML package and dependency groups in `pipelines/pyproject.toml`
- [X] T006 [P] Initialize the React TypeScript application and scripts in `frontend/package.json`
- [X] T007 [P] Configure Python linting, typing, and pytest defaults in `pyproject.toml`
- [X] T008 [P] Configure frontend formatting, linting, testing, and TypeScript in `frontend/eslint.config.js`
- [X] T009 Define PostgreSQL, API, pipeline, and frontend container builds in `compose.yaml`
- [X] T010 Add stable bootstrap, generation, pipeline, model, test, and benchmark targets in `Makefile`

**Checkpoint**: Dependency installation and placeholder health commands succeed from a clean clone.

---

## Phase 2: Foundational

**Purpose**: Build shared contracts, configuration, persistence, logging, and reproducibility support
that block every user story.

- [ ] T011 Add validated API settings and secret loading in `backend/src/fraud_api/core/config.py`
- [ ] T012 [P] Add structured JSON logging with sensitive-field redaction in `backend/src/fraud_api/core/logging.py`
- [ ] T013 [P] Add pipeline settings, deterministic seed handling, and artifact paths in `pipelines/src/fraud_pipelines/config.py`
- [ ] T014 Define shared feature names, types, bounds, defaults, and semantic version in `backend/src/fraud_api/features/definitions.py`
- [ ] T015 Mirror the registered feature contract for Spark jobs in `pipelines/src/fraud_pipelines/features/definitions.py`
- [ ] T016 Add golden feature fixtures shared across runtimes in `tests/fixtures/feature_parity.json`
- [ ] T017 Configure SQLAlchemy engine and transaction-scoped sessions in `backend/src/fraud_api/db/session.py`
- [ ] T018 Create Alembic configuration and migration environment in `backend/alembic/env.py`
- [ ] T019 Implement RFC 9457-style problem responses and exception mapping in `backend/src/fraud_api/api/errors.py`
- [ ] T020 Generate or hand-maintain frontend API types from the contract in `frontend/src/api/schema.ts`
- [ ] T021 Add API application startup, versioned routing, and health reporting in `backend/src/fraud_api/main.py`
- [ ] T022 Add API and database health integration tests in `backend/tests/integration/test_health.py`
- [ ] T023 Add Spark local-session and temporary artifact fixtures in `pipelines/tests/conftest.py`
- [ ] T024 Add PostgreSQL initialization and least-privilege application roles in `infra/postgres/init.sql`
- [ ] T025 Validate the OpenAPI document and generated application schema in `backend/tests/contract/test_openapi.py`

**Checkpoint**: Services start, database migrations run, health is truthful, and schema validation
passes before story work begins.

---

## Phase 3: User Story 1 — Score Incoming Transactions (P1) MVP

**Goal**: Accept a valid transaction idempotently and produce a persisted, versioned score or an
explicit scoring failure.

**Independent Test**: Submit valid, invalid, duplicated, conflicting, high-risk, and model-unavailable
transactions; verify terminal outcomes and database counts.

### Tests

- [ ] T026 [P] [US1] Add transaction validation and serialization tests in `backend/tests/unit/test_transaction_schemas.py`
- [ ] T027 [P] [US1] Add score band, threshold boundary, and explanation mapping tests in `backend/tests/unit/test_scoring.py`
- [ ] T028 [P] [US1] Add POST and GET transaction contract tests in `backend/tests/contract/test_transactions.py`
- [ ] T029 [P] [US1] Add idempotency, conflicting-payload, model-unavailable, and atomicity tests in `backend/tests/integration/test_transaction_ingestion.py`
- [ ] T030 [P] [US1] Add offline/online feature parity tests using golden fixtures in `backend/tests/integration/test_feature_parity.py`

### Implementation

- [ ] T031 [P] [US1] Implement account, merchant, transaction, feature snapshot, model version, fraud score, and alert tables in `backend/src/fraud_api/db/models.py`
- [ ] T032 [US1] Create the initial operational schema migration in `backend/alembic/versions/0001_scoring_core.py`
- [ ] T033 [P] [US1] Implement strict transaction input and scoring output schemas in `backend/src/fraud_api/schemas/transactions.py`
- [ ] T034 [P] [US1] Implement scalar online feature transformations in `backend/src/fraud_api/features/online.py`
- [ ] T035 [P] [US1] Implement versioned XGBoost artifact integrity checks and loading in `backend/src/fraud_api/models/loader.py`
- [ ] T036 [US1] Implement score probability, risk bands, thresholding, and contribution extraction in `backend/src/fraud_api/services/scoring.py`
- [ ] T037 [US1] Implement idempotent transaction persistence and payload conflict detection in `backend/src/fraud_api/repositories/transactions.py`
- [ ] T038 [US1] Implement atomic transaction, feature snapshot, score, and alert orchestration in `backend/src/fraud_api/services/ingestion.py`
- [ ] T039 [US1] Implement POST and GET transaction routes from the OpenAPI contract in `backend/src/fraud_api/api/routes/transactions.py`
- [ ] T040 [US1] Add sanitized scoring and failure events to structured logs in `backend/src/fraud_api/services/ingestion.py`
- [ ] T041 [US1] Add deterministic operational account and merchant seeding in `backend/src/fraud_api/db/seed.py`
- [ ] T042 [US1] Add a reproducible request fixture and idempotency smoke command in `tests/fixtures/transaction.json`

**Checkpoint**: User Story 1 is independently runnable and meets SC-001 and SC-002. This is the
first deployable API MVP.

---

## Phase 4: User Story 2 — Investigate High-Risk Activity (P2)

**Goal**: Give an analyst a prioritized queue, transparent score detail, and append-only review
workflow.

**Independent Test**: Load a fixed alert set, filter and inspect it, record two decisions, and verify
the original score plus complete history remain unchanged.

### Tests

- [ ] T043 [P] [US2] Add alert filtering, cursor ordering, and detail contract tests in `backend/tests/contract/test_alerts.py`
- [ ] T044 [P] [US2] Add alert state transition and append-only audit tests in `backend/tests/integration/test_alert_reviews.py`
- [ ] T045 [P] [US2] Add alert queue loading, empty, error, and filtering tests in `frontend/src/features/alerts/AlertQueue.test.tsx`
- [ ] T046 [P] [US2] Add explanation disclaimer and decision-history tests in `frontend/src/features/alerts/AlertDetail.test.tsx`

### Implementation

- [ ] T047 [P] [US2] Implement review decision and alert history tables in `backend/src/fraud_api/db/review_models.py`
- [ ] T048 [US2] Add review workflow schema migration in `backend/alembic/versions/0002_alert_reviews.py`
- [ ] T049 [P] [US2] Implement alert list, detail, history, and decision schemas in `backend/src/fraud_api/schemas/alerts.py`
- [ ] T050 [US2] Implement risk-descending cursor queries and filters in `backend/src/fraud_api/repositories/alerts.py`
- [ ] T051 [US2] Implement allowed alert transitions and append-only decisions in `backend/src/fraud_api/services/reviews.py`
- [ ] T052 [US2] Implement alert list, detail, status, and decision routes in `backend/src/fraud_api/api/routes/alerts.py`
- [ ] T053 [P] [US2] Implement the typed HTTP client and error mapping in `frontend/src/api/client.ts`
- [ ] T054 [P] [US2] Implement analyst application shell and navigation in `frontend/src/routes/AppRouter.tsx`
- [ ] T055 [US2] Implement risk queue filters, cursor pagination, empty state, and error state in `frontend/src/features/alerts/AlertQueue.tsx`
- [ ] T056 [US2] Implement transaction context, factor directions, disclaimer, and audit history in `frontend/src/features/alerts/AlertDetail.tsx`
- [ ] T057 [US2] Implement status and decision controls with pending and failure feedback in `frontend/src/features/alerts/ReviewControls.tsx`

**Checkpoint**: User Story 2 is independently demonstrable and a scripted analyst completes SC-003.

---

## Phase 5: User Story 3 — Monitor Fraud and Model Outcomes (P3)

**Goal**: Present reconciled operational charts and honest labeled model metrics for one UTC range.

**Independent Test**: Query a fixed seeded range and reconcile every total, bucket, risk band,
outcome, and model metric with source records.

### Tests

- [ ] T058 [P] [US3] Add dashboard range and model summary contract tests in `backend/tests/contract/test_dashboard.py`
- [ ] T059 [P] [US3] Add aggregate reconciliation and unlabeled-record tests in `backend/tests/integration/test_dashboard_metrics.py`
- [ ] T060 [P] [US3] Add dashboard loading, empty, failure, and chart accessibility tests in `frontend/src/features/dashboard/Dashboard.test.tsx`

### Implementation

- [ ] T061 [P] [US3] Implement UTC range, aggregate, series, and model metric schemas in `backend/src/fraud_api/schemas/dashboard.py`
- [ ] T062 [US3] Implement transaction, alert, amount, band, outcome, and time-bucket queries in `backend/src/fraud_api/repositories/dashboard.py`
- [ ] T063 [US3] Implement dashboard and active-model routes in `backend/src/fraud_api/api/routes/dashboard.py`
- [ ] T064 [P] [US3] Implement reusable accessible metric cards and chart states in `frontend/src/features/dashboard/components.tsx`
- [ ] T065 [US3] Implement range selection, summary cards, volume trend, risk distribution, and outcomes in `frontend/src/features/dashboard/Dashboard.tsx`
- [ ] T066 [US3] Implement model identity, threshold, confusion counts, precision, recall, PR-AUC, and no-label state in `frontend/src/features/dashboard/ModelPerformance.tsx`

**Checkpoint**: User Story 3 meets SC-004 and SC-005 against fixed reconciliation fixtures.

---

## Phase 6: User Story 4 — Build Reproducible Historical Features (P4)

**Goal**: Generate synthetic history and use Spark to produce point-in-time correct, reproducible
Parquet feature datasets and a trained model artifact.

**Independent Test**: Run fixed generation and feature configurations twice, compare manifests and
features, then train and verify the chronological evaluation and artifact metadata.

### Tests

- [ ] T067 [P] [US4] Add deterministic generator and fraud-scenario tests in `pipelines/tests/unit/test_generation.py`
- [ ] T068 [P] [US4] Add Spark schema validation, quarantine, and duplicate tests in `pipelines/tests/integration/test_validation_job.py`
- [ ] T069 [P] [US4] Add point-in-time feature and no-future-information tests in `pipelines/tests/integration/test_feature_job.py`
- [ ] T070 [P] [US4] Add repeated-run manifest and Parquet equivalence tests in `pipelines/tests/integration/test_reproducibility.py`
- [ ] T071 [P] [US4] Add chronological split, metric completeness, and artifact tests in `pipelines/tests/unit/test_training.py`

### Implementation

- [ ] T072 [P] [US4] Define strict Spark schemas for accounts, merchants, and transactions in `pipelines/src/fraud_pipelines/schemas/raw.py`
- [ ] T073 [P] [US4] Implement deterministic account and merchant generation in `pipelines/src/fraud_pipelines/generation/entities.py`
- [ ] T074 [US4] Implement chronological transaction generation with planted fraud scenarios in `pipelines/src/fraud_pipelines/generation/transactions.py`
- [ ] T075 [US4] Implement raw snapshot writing and fingerprinted bronze manifest creation in `pipelines/src/fraud_pipelines/generation/write.py`
- [ ] T076 [P] [US4] Implement reusable data-quality rules and quarantine reasons in `pipelines/src/fraud_pipelines/jobs/validation.py`
- [ ] T077 [US4] Implement Spark joins and point-in-time window features without Python UDFs in `pipelines/src/fraud_pipelines/jobs/features.py`
- [ ] T078 [US4] Implement partitioned Parquet output and dataset manifest hashing in `pipelines/src/fraud_pipelines/jobs/manifests.py`
- [ ] T079 [US4] Implement chronological train, validation, and test assignment in `pipelines/src/fraud_pipelines/training/splits.py`
- [ ] T080 [US4] Implement logistic baseline and XGBoost training with class weighting and early stopping in `pipelines/src/fraud_pipelines/training/train.py`
- [ ] T081 [US4] Implement PR-AUC evaluation, threshold trade-off reporting, and alert volume in `pipelines/src/fraud_pipelines/training/evaluate.py`
- [ ] T082 [US4] Implement JSON artifact, SHA-256, feature version, dataset ID, and metrics export in `pipelines/src/fraud_pipelines/training/artifacts.py`
- [ ] T083 [US4] Implement processing-run manifests and sanitized failure summaries in `pipelines/src/fraud_pipelines/jobs/run.py`
- [ ] T084 [US4] Wire generator, features, training, evaluation, and activation commands into `pipelines/src/fraud_pipelines/cli.py`

**Checkpoint**: User Story 4 meets SC-006 and provides the artifact consumed by User Story 1. For
delivery sequencing, a small checked test artifact may unblock US1; the real trained artifact replaces
it when this phase completes.

---

## Phase 7: Polish and Cross-Cutting Verification

**Purpose**: Prove the complete system, document the result, and support honest scale claims.

- [ ] T085 Add the highest-risk review browser journey in `tests/e2e/fraud-review.spec.ts`
- [ ] T086 [P] Add service and pipeline container health checks in `compose.yaml`
- [ ] T087 [P] Add dashboard accessibility and keyboard-navigation verification in `frontend/tests/accessibility.spec.ts`
- [ ] T088 Add the one-million-row benchmark runner and environment capture in `pipelines/src/fraud_pipelines/benchmark.py`
- [ ] T089 Add benchmark result schema and interpretation guidance in `docs/benchmarking.md`
- [ ] T090 Add architecture, data-flow, model-card, limitations, and troubleshooting documentation in `README.md`
- [ ] T091 Add model-card generation with dataset, metrics, threshold, intended use, and limitations in `pipelines/src/fraud_pipelines/training/model_card.py`
- [ ] T092 Run every command in `specs/001-fraud-review-platform/quickstart.md` and record verified output in `docs/verification.md`
- [ ] T093 Audit logs, fixtures, Git history, and artifacts for secrets or identifying financial data in `docs/security-audit.md`
- [ ] T094 Reconcile implementation against all requirements and acceptance scenarios in `specs/001-fraud-review-platform/checklists/implementation.md`

---

## Dependencies and Execution Order

### Phase dependencies

```text
Setup (1) -> Foundation (2) -> US1 scoring MVP (3)
                               |-> US2 review (4) -> US3 dashboard (5)
Foundation (2) -> US4 batch/ML (6) -> production-like model used by US1
US1 + US2 + US3 + US4 -> Polish and verification (7)
```

- Setup and Foundation block all story work.
- US1 is the first deployable vertical slice and may use a deterministic test model artifact.
- US2 depends on alerts produced by US1.
- US3 depends on operational records from US1 and review outcomes from US2.
- US4 can proceed after Foundation and is otherwise independent; it replaces the test artifact with
  the reproducibly trained model and proves Spark's role.
- Final end-to-end and benchmark verification depends on all selected stories.

### Parallel opportunities

- T004–T008 can proceed independently after the root structure exists.
- T012–T016 and T023–T024 touch separate concerns after configuration conventions are fixed.
- Tests marked `[P]` within each user story can be authored concurrently before implementation.
- After Foundation, US4 pipeline work can proceed in parallel with the US1 application slice.
- Frontend component work can proceed after the story's contract schemas stabilize.

## Implementation Strategy

### MVP first

Complete Phases 1–3 and validate User Story 1. This produces a real transaction-to-score path with
idempotency, persistence, model/feature traceability, alerts, and explicit failure behavior.

### Incremental delivery

1. Commit Setup only after clean-clone bootstrap checks pass.
2. Commit Foundation when health, migrations, logging, and contract validation pass.
3. Commit US1 as the scoring MVP and demonstrate its independent acceptance tests.
4. Add US2 and US3 as analyst-facing vertical slices with frontend and backend tests together.
5. Build US4 as the Spark/ML slice, then activate its artifact through the already-tested API.
6. Finish with cross-system, accessibility, security, documentation, and benchmark evidence.

Each checkpoint gets a focused commit and push only after its documented checks pass.
