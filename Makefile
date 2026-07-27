PNPM ?= pnpm

.PHONY: bootstrap check lint test test-integration test-e2e compose-config \
	generate-demo features verify-features train evaluate activate-model \
	seed-operational-data smoke-score benchmark migrate

bootstrap:
	uv sync --project backend --all-groups
	uv sync --project pipelines --all-groups
	$(PNPM) --dir frontend install

check: lint test compose-config

lint:
	uv run --project backend ruff check backend/src backend/tests
	uv run --project pipelines ruff check pipelines/src pipelines/tests
	$(PNPM) --dir frontend run lint

test:
	uv run --project backend pytest backend/tests/unit
	uv run --project pipelines pytest pipelines/tests/unit
	$(PNPM) --dir frontend test

test-integration:
	uv run --project backend pytest -m integration backend/tests
	uv run --project pipelines pytest -m integration pipelines/tests

test-e2e:
	@echo "E2E tests become available in Phase 7."

compose-config:
	docker compose --env-file .env.example config --quiet

generate-demo:
	uv run --project pipelines fraud-pipelines generate --seed $(or $(SEED),20260727) --rows $(or $(ROWS),50000)

features:
	uv run --project pipelines fraud-pipelines features

verify-features:
	uv run --project pipelines pytest pipelines/tests/integration/test_feature_job.py

train:
	uv run --project pipelines fraud-pipelines train

evaluate:
	uv run --project pipelines fraud-pipelines evaluate

activate-model:
	uv run --project pipelines fraud-pipelines activate-model

seed-operational-data:
	uv run --project backend python -m fraud_api.db.seed

smoke-score:
	@echo "Smoke scoring becomes available with User Story 1."

benchmark:
	uv run --project pipelines fraud-pipelines benchmark --seed $(or $(SEED),20260727) --rows $(or $(ROWS),1000000)

migrate:
	uv run --project backend alembic upgrade head
