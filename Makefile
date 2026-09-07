COMPOSE = docker compose --env-file backend/.env -f compose.yaml

.PHONY: setup dev down check migrate test lint
setup:
	python3 backend/scripts/dev_setup.py
	cd backend && uv sync --locked

dev: setup
	$(COMPOSE) up --build --wait

down:
	$(COMPOSE) down

check:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run pytest -q

migrate:
	cd backend && uv run alembic upgrade head

test:
	cd backend && uv run pytest -q

lint:
	cd backend && uv run ruff check . && uv run ruff format --check .
