.PHONY: bootstrap fmt lint mypy pyright pylance check run clean

bootstrap:
	uv sync --dev

fmt:
	uv run ruff format .

lint:
	uv run ruff check . --fix

mypy:
	uv run mypy

pyright:
	uv run pyright

pylance: pyright

typecheck: mypy pyright

check: lint fmt typecheck

run:
	uv run uvicorn template.main:app --reload --port 8000

clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache
