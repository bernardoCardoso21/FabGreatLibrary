# ── Shell (works in Git Bash on Windows and Linux/macOS) ──────────────────────
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

# ── Paths ─────────────────────────────────────────────────────────────────────
COMPOSE_FILE := infra/docker/docker-compose.yml

# Venv binary directory differs between Windows and Unix
ifeq ($(OS),Windows_NT)
  VENV_BIN := apps/api/.venv/Scripts
else
  VENV_BIN := apps/api/.venv/bin
endif

PYTHON  := $(VENV_BIN)/python
PYTEST  := $(VENV_BIN)/pytest
ALEMBIC := $(VENV_BIN)/alembic
UVICORN := $(VENV_BIN)/uvicorn

# ── Infrastructure ─────────────────────────────────────────────────────────────
.PHONY: up
up: ## Start Postgres (detached)
	docker compose -f $(COMPOSE_FILE) up -d

.PHONY: up-tools
up-tools: ## Start Postgres + pgAdmin
	docker compose -f $(COMPOSE_FILE) --profile tools up -d

.PHONY: down
down: ## Stop all Compose services
	docker compose -f $(COMPOSE_FILE) --profile tools down

.PHONY: logs
logs: ## Tail Compose logs
	docker compose -f $(COMPOSE_FILE) logs -f

# ── Backend ────────────────────────────────────────────────────────────────────
.PHONY: api-install
api-install: ## Create venv and install API dependencies
	cd apps/api && python -m venv .venv && $(PYTHON) -m pip install --upgrade pip && $(PYTHON) -m pip install -e ".[dev]"

.PHONY: api-dev
api-dev: ## Run FastAPI dev server (port 8000, hot-reload)
	cd apps/api && $(UVICORN) app.main:app --reload --port 8000

.PHONY: migrate
migrate: ## Run Alembic migrations (upgrade head)
	cd apps/api && $(ALEMBIC) upgrade head

.PHONY: migrate-down
migrate-down: ## Rollback one Alembic migration
	cd apps/api && $(ALEMBIC) downgrade -1

.PHONY: seed
seed: ## Seed the dev database (idempotent)
	cd apps/api && $(PYTHON) -m scripts.seed

.PHONY: import-cards
import-cards: ## Import FAB card data from the-fab-cube dataset (uses CARDS_DATA_VERSION)
	cd apps/api && $(PYTHON) -m scripts.import_cards

.PHONY: test
test: ## Run backend pytest suite
	cd apps/api && $(PYTEST) -v

# ── Frontend ───────────────────────────────────────────────────────────────────
.PHONY: web-install
web-install: ## Install frontend npm dependencies
	cd apps/web && npm install

.PHONY: web-dev
web-dev: ## Run Next.js dev server (port 3000, hot-reload)
	cd apps/web && npm run dev

.PHONY: web-build
web-build: ## Production build of the frontend
	cd apps/web && npm run build

# ── Convenience ────────────────────────────────────────────────────────────────
.PHONY: install
install: api-install web-install ## Install all dependencies (api + web)

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
