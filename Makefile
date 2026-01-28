.PHONY: bootstrap fmt lint ty ty-watch mypy typecheck check run clean

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

check: lint fmt typecheck

run:
	uv run uvicorn template.main:app --reload --port 8000

clean:
	rm -rf .pytest_cache .ruff_cache
