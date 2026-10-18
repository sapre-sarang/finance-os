# FinanceOS developer tasks. Run `make` or `make help` to list them.
# Needs: uv (https://docs.astral.sh/uv/), Node.js LTS and pnpm, and a running Postgres
# (see packages/db/README.md). Recipes avoid `cd` so they work from any shell.

CORE := packages/core
DB   := packages/db
API  := apps/api
WEB  := apps/web

.DEFAULT_GOAL := help

.PHONY: help setup migrate create-user api web dev \
        test test-core test-api test-web \
        lint format typecheck build check clean

help:
	@echo FinanceOS tasks:
	@echo   make setup                       Install all Python and web dependencies
	@echo   make migrate                     Apply database migrations to the dev database
	@echo   make create-user APP_USER=name   Create the sign-in (prompts for a password)
	@echo   make api                         Run the API on http://127.0.0.1:8000
	@echo   make web                         Run the web app on http://127.0.0.1:5173
	@echo   make dev                         Run API and web together (make -j2)
	@echo   make test                        Run core, API and web tests
	@echo   make lint                        Ruff on all Python packages
	@echo   make format                      Ruff format on all Python packages
	@echo   make typecheck                   mypy (strict) and tsc
	@echo   make build                       Production build of the web app
	@echo   make check                       lint + typecheck + test (run before committing)
	@echo   make clean                       Remove caches and build output

setup:
	uv --directory $(CORE) sync
	uv --directory $(DB) sync
	uv --directory $(API) sync
	pnpm --dir $(WEB) install

migrate:
	uv --directory $(API) run python -m app.cli migrate

create-user:
	$(if $(APP_USER),,$(error Usage: make create-user APP_USER=<username>))
	uv --directory $(API) run python -m app.cli create-user $(APP_USER)

api:
	uv --directory $(API) run uvicorn --factory app.main:create_app --reload --host 127.0.0.1 --port 8000

web:
	pnpm --dir $(WEB) dev

dev:
	$(MAKE) -j2 api web

test: test-core test-api test-web

test-core:
	uv --directory $(CORE) run pytest -q

test-api:
	uv --directory $(API) run pytest -q

test-web:
	pnpm --dir $(WEB) test

lint:
	uv --directory $(CORE) run ruff check
	uv --directory $(DB) run ruff check
	uv --directory $(API) run ruff check

format:
	uv --directory $(CORE) run ruff format
	uv --directory $(DB) run ruff format
	uv --directory $(API) run ruff format

typecheck:
	uv --directory $(CORE) run mypy
	uv --directory $(DB) run mypy
	uv --directory $(API) run mypy
	pnpm --dir $(WEB) typecheck

build:
	pnpm --dir $(WEB) build

check: lint typecheck test

clean:
	uv --directory $(CORE) run python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for name in ('.pytest_cache', '.mypy_cache', '.ruff_cache', 'dist') for p in pathlib.Path('../..').glob('*/*/' + name)]"
