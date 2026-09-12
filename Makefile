COMPOSE = docker compose --env-file backend/.env -f compose.yaml

.PHONY: setup dev down check migrate test lint coverage audit hooks hooks-check requirements-check
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

coverage:
	cd backend && uv run pytest --cov --cov-report=term-missing --cov-report=xml --cov-report=html

audit:
	cd backend && uv run pip-audit --strict

hooks:
	cd backend && uv run pre-commit install

hooks-check:
	cd backend && uv run pre-commit run --all-files

requirements-check:
	python3 backend/scripts/check_requirements.py

.PHONY: demo admin
demo:
	cd backend && uv run python -m app.bootstrap seed-demo --confirm-demo

admin:
	cd backend && uv run python -m app.bootstrap admin --email "$(EMAIL)"

.PHONY: frontend frontend-check
frontend:
	cd frontend && npm ci && npm run dev

frontend-check:
	cd frontend && npm run format:check && npm run lint && npm run typecheck && npm test && npm run build && npm run test:e2e
