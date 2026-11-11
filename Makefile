UV ?= uv
PNPM ?= pnpm
DOCKER ?= docker
TEST_DATABASE_URL ?= postgresql+psycopg://lingora:lingora_test_local@localhost:5433/lingora_test

.PHONY: setup db-up db-down db-test-up migrate dev-api dev-web api-generate test test-api test-integration test-web test-e2e lint typecheck build audit check

setup:
	@test -f .env || cp .env.example .env
	@test -f apps/web/.env.local || cp apps/web/.env.example apps/web/.env.local
	$(UV) sync --project apps/api --locked
	$(PNPM) install --frozen-lockfile

db-up:
	$(DOCKER) compose up -d --wait db

db-down:
	$(DOCKER) compose --profile test down

db-test-up:
	$(DOCKER) compose --profile test up -d --wait db-test

migrate:
	$(UV) run --project apps/api alembic -c apps/api/alembic.ini upgrade head

dev-api:
	$(UV) run --project apps/api uvicorn lingora.main:app --host 127.0.0.1 --port 8000 --reload --no-access-log

dev-web:
	$(PNPM) --filter @lingora/web dev

ingest-content:
	$(UV) run --project apps/api python -m lingora.learning_cli ingest

dev-worker:
	$(UV) run --project apps/api python -m lingora.learning_cli worker

dev-mcp:
	$(UV) run --project apps/api uvicorn lingora.mcp_main:app --host 127.0.0.1 --port 8080 --no-access-log

api-generate:
	$(UV) run --project apps/api python apps/api/scripts/export_openapi.py
	$(PNPM) --filter @lingora/api-client generate

test: test-api test-web

test-api:
	$(UV) run --project apps/api pytest apps/api/tests --ignore=apps/api/tests/integration

test-integration: db-test-up
	TEST_DATABASE_URL='$(TEST_DATABASE_URL)' $(UV) run --project apps/api pytest apps/api/tests/integration

test-web:
	$(PNPM) test
	node --test infra/auth0/*.test.cjs

test-e2e:
	$(PNPM) test:e2e

lint:
	$(UV) run --project apps/api ruff check apps/api
	$(UV) run --project apps/api ruff format --check apps/api
	$(PNPM) lint

typecheck:
	$(UV) run --project apps/api pyright --project apps/api/pyproject.toml
	$(PNPM) typecheck

build:
	$(PNPM) build

audit:
	$(UV) run --project apps/api pip-audit --skip-editable
	$(PNPM) audit --prod --audit-level high

check: lint typecheck test test-integration build test-e2e
