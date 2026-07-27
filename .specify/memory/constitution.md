<!--
Sync Impact Report
- Version change: template -> 1.0.0
- Modified principles: all template placeholders replaced with project-specific principles
- Added sections: Architecture & Data Constraints; Delivery & Quality Gates
- Removed sections: none
- Templates updated:
  - ✅ .specify/templates/plan-template.md
  - ✅ .specify/templates/spec-template.md
  - ✅ .specify/templates/tasks-template.md
- Follow-up TODOs: none
-->
# Fraud Detection Platform Constitution

## Core Principles

### I. Spark Earns Its Place
Spark MUST perform the platform's large-scale historical processing: ingestion, validation,
joins, feature engineering, aggregation, and Parquet production. Batch pipelines MUST be
executable on small local fixtures and designed to scale to millions of synthetic transactions.
Spark MUST NOT be placed in the synchronous HTTP scoring path; FastAPI loads a versioned model
artifact for low-latency predictions. Structured Streaming and Kafka are later increments, not
MVP prerequisites. This keeps Spark central where distributed computation is credible without
making the application needlessly slow or fragile.

### II. Reproducible and Honest ML
Every dataset, feature definition, split strategy, model configuration, metric, threshold, and
artifact MUST be reproducible from version-controlled code and configuration. Time-aware splits
MUST be used where chronology exists, and features MUST use only information available at scoring
time. Model evaluation MUST report precision, recall, PR-AUC, confusion counts, and alert volume;
accuracy alone is forbidden as evidence of fraud-model quality. Explanations MUST describe model
influence rather than claim causation. These rules prevent leakage and misleading portfolio claims.

### III. Privacy and Financial-System Safety
Development MUST use public, anonymized, or synthetic data only; secrets, payment credentials,
and personally identifiable financial data MUST NOT enter the repository or logs. Inputs MUST be
validated at trust boundaries, database access MUST be parameterized, and secrets MUST come from
ignored environment configuration. Fraud decisions MUST remain reviewable: a score or alert is a
risk signal, not an autonomous accusation or irreversible financial action.

### IV. Contracts, Traceability, and Observability
API schemas, database migrations, event shapes, feature definitions, and model metadata MUST be
explicit and versioned. Every scored transaction MUST be traceable to its model version and retain
the information required to reproduce the prediction. Services and pipelines MUST emit structured
logs and actionable errors without exposing sensitive fields. Contract changes MUST include
compatibility analysis and integration tests so the Spark, API, database, model, and dashboard
boundaries remain dependable.

### V. Tested Incremental Delivery
Work MUST proceed as independently demonstrable vertical slices, starting with a batch-scored MVP.
Behavior changes MUST have automated tests at the lowest effective level, with contract and
integration tests at service boundaries. Each milestone MUST include documented verification,
updated setup instructions, and a focused commit. Optional infrastructure such as Kafka, Redis,
MLflow, monitoring, and automated retraining MUST be introduced only through a specification with
measurable value and acceptance criteria.

## Architecture & Data Constraints

- The baseline stack is Python, PySpark, XGBoost or LightGBM, FastAPI, PostgreSQL, React with
  TypeScript, Parquet, and Docker Compose.
- PostgreSQL is the operational store for transactions, scores, alerts, and investigation state;
  Parquet is the analytical interchange and training format.
- Training and batch feature pipelines own historical feature computation. Online scoring MUST
  use an explicitly compatible transformation path and MUST test offline/online feature parity.
- Synthetic generation MUST support understandable fraud scenarios and deterministic seeds. A
  public dataset MAY supplement model validation, but the project MUST remain runnable without
  committing a large or restricted dataset.
- Performance or scale claims MUST be backed by a repeatable benchmark including data volume,
  hardware context, configuration, and observed results.

## Delivery & Quality Gates

Each feature specification MUST define prioritized user journeys, edge cases, measurable outcomes,
data sensitivity, model-risk considerations when applicable, and explicit exclusions. Plans MUST
pass the constitution check before implementation and again after design. Tasks MUST include tests,
schema or contract validation, observability, documentation, and reproducibility work required by
the feature. Before a milestone commit, relevant formatting, static analysis, unit tests, contract
tests, and integration tests MUST pass; any unavailable check MUST be documented with its reason.

## Governance

This constitution governs all specifications, plans, tasks, and implementation choices. An
amendment requires a documented rationale, a Sync Impact Report, updates to dependent templates,
and an explicit semantic-version change: MAJOR for incompatible governance changes, MINOR for new
or materially expanded principles, and PATCH for non-semantic clarification. Every plan and review
MUST verify compliance. Any exception MUST be recorded in the plan's Complexity Tracking table with
the rejected simpler option and a removal or review condition.

**Version**: 1.0.0 | **Ratified**: 2026-07-27 | **Last Amended**: 2026-07-27
