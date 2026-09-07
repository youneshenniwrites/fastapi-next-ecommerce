# Prefer the root Makefile for full-stack commands.
.PHONY: run init-db test
run:
	uv run uvicorn app.main:app --reload
init-db:
	uv run alembic upgrade head
test:
	uv run pytest -q
