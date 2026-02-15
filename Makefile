.PHONY: bootstrap fmt lint ty ty-watch mypy typecheck check pytest run clean

bootstrap:
	uv sync --dev

fmt:
	uv run ruff format .

lint:
	uv run ruff check . --fix

ty:
	uv run ty check --error-on-warning

ty-watch:
	uv run ty check --watch --error-on-warning

mypy:
	uv run mypy

typecheck: ty mypy

check: lint fmt typecheck pytest

pytest:
	uv run pytest

run:
	uv run uvicorn --app-dir src backend.main:create_app --factory --reload --port 8000

clean:
	rm -rf .pytest_cache .ruff_cache
