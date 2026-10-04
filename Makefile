# Finance Hub. Backend in ./backend (FastAPI), frontend in ./frontend (Angular), Postgres via compose.
.DEFAULT_GOAL := help
SHELL := /bin/bash

BACKEND := backend
FRONTEND := frontend
VENV := $(BACKEND)/.venv
PY := $(VENV)/bin/python
UVICORN := $(VENV)/bin/uvicorn
ALEMBIC := $(VENV)/bin/alembic
PYTEST := $(VENV)/bin/pytest

.PHONY: deploy deploy-setup help install install-backend install-frontend db-up db-down db-wait migrate revision \
        downgrade dev dev-backend dev-frontend test test-backend test-frontend lint

help: ## List targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: install-backend install-frontend ## Install backend and frontend dependencies

install-backend: ## Create backend/.venv and install the API with dev extras
	cd $(BACKEND) && (test -d .venv || (command -v uv >/dev/null && uv venv .venv) || python3 -m venv .venv)
	cd $(BACKEND) && (command -v uv >/dev/null && uv pip install --python .venv/bin/python -e ".[dev]" || .venv/bin/pip install -e ".[dev]")

install-frontend: ## npm install the Angular app
	cd $(FRONTEND) && npm install

db-up: ## Start Postgres in Docker
	docker compose up -d db

db-down: ## Stop Postgres (data volume kept)
	docker compose down

db-wait: ## Block until Postgres accepts connections
	@until $(PY) -c "import psycopg,os; psycopg.connect(os.environ.get('HUB_DATABASE_URL','postgresql://hub:hub@localhost:5432/finance_hub')).close()" 2>/dev/null; do echo "waiting for postgres..."; sleep 1; done

migrate: ## Apply Alembic migrations to the dev database
	cd $(BACKEND) && .venv/bin/alembic upgrade head

downgrade: ## Roll back one migration
	cd $(BACKEND) && .venv/bin/alembic downgrade -1

revision: ## Autogenerate a migration: make revision m="add thing"
	cd $(BACKEND) && .venv/bin/alembic revision --autogenerate -m "$(m)"

dev: db-up db-wait migrate ## Start database, migrate, then run API (8000) and Angular (4200) together
	@trap 'kill 0' INT TERM EXIT; \
	$(MAKE) --no-print-directory dev-backend & \
	$(MAKE) --no-print-directory dev-frontend & \
	wait

dev-backend: ## Run the API with reload on :8000
	cd $(BACKEND) && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Run the Angular dev server on :4200 (proxies /api to :8000)
	cd $(FRONTEND) && npx ng serve --host 0.0.0.0 --port 4200

test: test-backend test-frontend ## Run backend and frontend tests

test-backend: ## pytest (migrates finance_hub_test up and back down)
	cd $(BACKEND) && .venv/bin/pytest

test-frontend: ## Angular unit tests, single run
	cd $(FRONTEND) && npx ng test --watch=false

lint: ## ruff check + format check on the backend
	cd $(BACKEND) && .venv/bin/ruff check . && .venv/bin/ruff format --check .

deploy: ## Deploy to Fly.io by hand; normally Fly's GitHub integration deploys on push to main
	fly deploy --remote-only

deploy-setup: ## CLI alternative to the dashboard's Launch from GitHub: app, Postgres, secrets
	fly apps create finance-hub || true
	fly postgres create --name finance-hub-db --region ord --vm-size shared-cpu-1x --volume-size 1 --initial-cluster-size 1
	fly postgres attach finance-hub-db --app finance-hub
	@echo "Now set the login:  fly secrets set HUB_BASIC_AUTH=you:a-long-password --app finance-hub"
