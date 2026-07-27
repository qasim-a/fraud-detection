# Verification Record

Verified locally on 2026-07-27 from commit `db72618` plus the fixes documented by this increment.
Host: macOS 26.5.2, ARM64, 8 logical CPUs, Python 3.12.4, Spark 4.2.0. Docker services were
shut down after verification; generated evidence remains under ignored `artifacts/`.

## Quickstart results

1. `cp .env.example .env` and `make bootstrap` passed. Both uv environments were synchronized and
   pnpm reported the frontend dependencies current.
2. `docker compose up --build -d postgres api frontend` built all images. `make migrate` applied
   migrations `0001_scoring_core` and `0002_alert_reviews`. PostgreSQL, API, and frontend all
   reported healthy. The API initially reported `model: unavailable`, as expected.
3. `make generate-demo SEED=20260727 ROWS=50000` passed twice with the same dataset ID
   `d839687f5947a49d2dab2a4f21fcd2e32316bbfabdbfe426a6107ba4ea4bc5a1` and identical account,
   merchant, and transaction hashes.
4. `make features` processed 50,000 rows with 0 rejected and produced dataset ID
   `5e5d6e016f69d32d4933e8b9e6fe19f5cb3d590f90ed380756207151a6da2853`. `make verify-features`
   passed the point-in-time Spark test.
5. `make train`, `make evaluate`, and `make activate-model` passed. Model
   `fraud-xgb-5e5d6e016f69` used threshold `0.2224537432`; chronological test metrics were precision
   `0.6557`, recall `1.0`, PR-AUC `1.0`, TP `160`, FP `84`, TN `7256`, FN `0`, and alert volume
   `244`. API health then reported the model available.
6. `make seed-operational-data` seeded two accounts and two merchants. Two `make smoke-score` calls
   returned the same transaction, score, and alert IDs. The database retained exactly one
   transaction, one score, and one alert.
7. The live Docker dashboard loaded one transaction, one alert, amount at risk, accessible volume
   and risk charts, and the active model metrics. The highest-risk alert showed transaction context,
   higher/lower influence factors, the non-causality disclaimer, and immutable model identity. A
   `needs_review` decision followed by `confirmed_fraud` remained visible as two audit events while
   the original 88% score remained unchanged.
8. `make lint`, `make test`, `make test-integration`, and `make test-e2e` passed: 17 backend unit,
   6 pipeline unit, 8 frontend, 11 backend integration, 4 Spark integration, and 2 Playwright tests.
9. `make benchmark ROWS=1000000 SEED=20260727` passed with 1,000,000 processed and 0 rejected in
   64.383 seconds total (12.911 generation, 46.649 Spark processing). Parquet output was 207,852,529
   bytes. Input fingerprint was `3523afdb39f6ef85d933fa21fad7e5f6d7723c87825f10a6219ca71cc743c787`;
   output fingerprint was `50c17d281fe591af1b1333ff20ec01e90bdb82b2749bf5236b565fb91874ca3d`.
10. `docker compose down` completed after the final checks.

## Success and failure evidence

- SC-001: 100 idempotent local scoring requests completed under two seconds (100%); maximum was
  `0.024863s` and mean was `0.004551s`.
- Model unavailable: a new valid transaction returned HTTP 503 with `scoring_failed`,
  `failureCode: model_unavailable`, and null score/alert; the model was then restored.
- Invalid amount: HTTP 422 identified `body.amount` and no completed transaction was created.
- Conflicting retry: changing the amount under the accepted UUID returned HTTP 409 and preserved
  the original row.
- Empty range: HTTP 200 returned zero transactions/alerts and an empty series, which the frontend
  renders as an empty chart state.

## Defects found and resolved during verification

- Split host and container database/artifact configuration so local commands use `localhost` and
  containers use Compose DNS plus `/artifacts`.
- Defaulted the project PostgreSQL host port to 5433 to avoid collision with a local server on 5432.
- Corrected frontend and API container health probes.
- Added the missing Vite `/api` proxy so the real dashboard reaches FastAPI through Compose.
- Corrected the integration-test marker placement detected by the documented lint command.
