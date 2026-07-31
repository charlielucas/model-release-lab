.PHONY: install check test lint build dev-api dev-ui demo

install:
	uv sync --extra dev
	cd frontend && npm ci

check: lint test build

test:
	uv run pytest
	cd frontend && npm test

lint:
	uv run ruff check .
	uv run ruff format --check .
	cd frontend && npm run typecheck

build:
	uv build
	cd frontend && npm run build

dev-api:
	uv run uvicorn model_release_lab.api:app --reload

dev-ui:
	cd frontend && npm run dev

demo:
	uv run model-release-lab clean-release
