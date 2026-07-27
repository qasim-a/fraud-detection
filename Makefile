PNPM ?= pnpm

.PHONY: bootstrap check lint typecheck build test test-contract test-integration test-e2e compose-config \
	generate-demo features verify-features train evaluate activate-model \
	seed-operational-data smoke-score benchmark migrate

bootstrap:
	uv sync --project backend --all-groups
	uv sync --project pipelines --all-groups
	$(PNPM) --dir frontend install

check: lint typecheck test test-contract build compose-config

lint:
	uv run --project backend ruff check backend/src backend/tests
	uv run --project pipelines ruff check pipelines/src pipelines/tests
	$(PNPM) --dir frontend run lint

typecheck:
	uv run --project backend pyright backend/src
	uv run --project pipelines pyright pipelines/src

build:
	$(PNPM) --dir frontend run build

test:
	uv run --project backend pytest backend/tests/unit
	uv run --project pipelines pytest pipelines/tests/unit
	$(PNPM) --dir frontend test

test-contract:
	uv run --project backend pytest backend/tests/contract

test-integration:
	uv run --project backend pytest -m integration backend/tests
	uv run --project pipelines pytest -m integration pipelines/tests

test-e2e:
	$(PNPM) --dir frontend exec playwright test

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
	curl --fail-with-body --silent --show-error \
		-H 'Content-Type: application/json' \
		--data @tests/fixtures/transaction.json \
		http://localhost:$${API_PORT:-8000}/api/v1/transactions

benchmark:
	uv run --project pipelines fraud-pipelines benchmark --seed $(or $(SEED),20260727) --rows $(or $(ROWS),1000000)

migrate:
	uv run --project backend alembic -c backend/alembic.ini upgrade head
