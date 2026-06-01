.PHONY: help setup dev down test test-unit test-integration lint format typecheck \
        db-migrate db-seed db-reset clean docker-up docker-down logs shell

PYTHON ?= python3.12
VENV   ?= .venv
PIP    := $(VENV)/bin/pip
PY     := $(VENV)/bin/python

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## First-time setup: create venv, install deps, copy .env
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	@test -f .env || cp .env.example .env
	@echo ""
	@echo "✓ Setup complete. Next: make docker-up && make db-migrate && make db-seed"

dev: ## Start dev server (assumes docker-up + migrations done)
	$(VENV)/bin/uvicorn fittrack.main:app --host 0.0.0.0 --port 8000 --reload

docker-up: ## Start Oracle Free + Redis containers; wait for Oracle ready
	docker compose -f docker/docker-compose.yml up -d
	@echo "Waiting for Oracle to become ready (this can take ~60s on first start)..."
	@./scripts/wait_for_oracle.sh

docker-down: ## Stop containers
	docker compose -f docker/docker-compose.yml down

logs: ## Tail container logs
	docker compose -f docker/docker-compose.yml logs -f

shell: ## SQL*Plus shell into the dev DB
	docker compose -f docker/docker-compose.yml exec oracle sqlplus fittrack_app/$$(grep '^ORACLE_PASSWORD' .env | cut -d= -f2)@//localhost:1521/FREEPDB1

db-migrate: ## Apply pending migrations
	$(PY) -m fittrack.database.migrations apply

db-seed: ## Populate synthetic data
	$(PY) scripts/seed_data.py

db-reset: ## Drop user data + re-migrate + re-seed (destructive)
	$(PY) scripts/reset_db.py

test: ## Run full test suite with coverage gate
	$(VENV)/bin/pytest

test-unit: ## Unit tests only (no DB required)
	$(VENV)/bin/pytest -m unit --no-cov

test-integration: ## Integration tests (requires running Oracle)
	$(VENV)/bin/pytest -m integration

lint: ## Lint (ruff + black --check)
	$(VENV)/bin/ruff check src tests scripts
	$(VENV)/bin/black --check src tests scripts

format: ## Auto-format with ruff + black
	$(VENV)/bin/ruff check --fix src tests scripts
	$(VENV)/bin/black src tests scripts

typecheck: ## mypy strict
	$(VENV)/bin/mypy src

clean: ## Remove caches, build artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage coverage.xml htmlcov
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +
