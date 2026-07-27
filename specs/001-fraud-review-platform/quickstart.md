# Quickstart Validation Guide: Fraud Review Platform

This guide defines the end-to-end evidence required once implementation exists. Commands are the
target developer interface and must remain stable or be updated here in the same change.

## Prerequisites

- Docker Desktop or Docker Engine with Compose v2
- `make`
- Node.js 22 and pnpm
- `uv`
- At least 8 GB available memory and 10 GB free disk for the quick demo
- For running pipelines outside Docker: Python 3.12 and Java 17

No external dataset is required. The canonical quickstart uses deterministic synthetic data.

## 1. Configure and start services

```bash
cp .env.example .env
make bootstrap
docker compose up --build -d postgres api frontend
make migrate
```

Expected result: PostgreSQL, API, and frontend report healthy. The API health response may report
the model as unavailable until training and activation complete.

## 2. Generate deterministic demo history

```bash
make generate-demo SEED=20260727 ROWS=50000
```

Expected result: synthetic account, merchant, and transaction snapshots appear below
`artifacts/bronze/`, accompanied by a manifest recording the seed, schema, counts, and fingerprints.
Running the command again with identical arguments produces the same identities and data hashes.

## 3. Build historical features

```bash
make features
make verify-features
```

Expected result: Spark produces validated Parquet under `artifacts/features/`, isolates deliberately
invalid fixture rows, and records lineage and quality counts. Verification repeats the fixed fixture
and confirms output parity and point-in-time correctness.

## 4. Train and activate the demonstration model

```bash
make train
make evaluate
make activate-model
```

Expected result: a model JSON file and metadata manifest appear below `artifacts/models/`. Evaluation
reports chronological split boundaries, precision, recall, PR-AUC, confusion counts, selected
threshold, and alert volume. Activation changes API health to show the versioned model as available.

## 5. Score a transaction and verify idempotency

```bash
make seed-operational-data
make smoke-score
make smoke-score
```

Expected result: the first call persists one transaction and a traceable score. The second identical
call returns the same transaction result without increasing transaction, score, or alert counts.
The response includes model version, feature version, threshold, risk band, and scoring time.

## 6. Complete the analyst journey

Open `http://localhost:5173` and:

1. Confirm the dashboard totals and charts load for the seeded range.
2. Open the alert queue and select the highest-risk unreviewed item.
3. Inspect transaction context and higher/lower contributing factors.
4. Confirm the explanation states that influence is not proof or cause.
5. Record a `needs_review` decision, then a final `confirmed_fraud` or `legitimate` decision.
6. Confirm both decisions remain in the audit history and the original prediction is unchanged.

## 7. Run automated verification

```bash
make lint
make test
make test-integration
make test-e2e
```

Expected result: formatting, static analysis, backend and pipeline unit tests, Spark/PostgreSQL
integration tests, frontend tests, OpenAPI contract validation, and the primary browser journey pass.

## 8. Run the scale benchmark

```bash
make benchmark ROWS=1000000 SEED=20260727
```

Expected result: the report records hardware context, Spark configuration, elapsed time, processed
and rejected counts, output size, schema and feature versions, and input/output fingerprints. It is
evidence for a local run, not a general production-throughput claim.

## Failure checks

- Stop or remove the model artifact and submit a valid new transaction: the transaction must enter
  `scoring_failed`; no fake probability or alert may appear.
- Submit a malformed amount or timestamp: the response must identify the invalid field and no
  completed transaction may be stored.
- Reuse a transaction UUID with a changed amount: the response must be a conflict and the original
  transaction must remain unchanged.
- Select a range with no data: charts must show an empty state, not zeros presented as observed data.

## Shutdown

```bash
docker compose down
```

Generated contents under `artifacts/` remain for inspection and are ignored by Git.
