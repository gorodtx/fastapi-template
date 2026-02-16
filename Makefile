.PHONY: fmt lint typecheck check pytest run clean

fmt:
	uv run ruff format .

lint:
	uv run ruff check . --fix

typecheck:
	uv run ty check --error-on-warning

check: lint fmt typecheck pytest

pytest:
	uv run pytest

run:
	uv run --no-dev --no-sync --frozen uvicorn --app-dir src backend.main:create_app --factory --host 0.0.0.0 --port 8000

clean:
	rm -rf .pytest_cache .ruff_cache
