.PHONY: bootstrap fmt lint mypy pyright pylance typecheck test check run clean

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

test:
	uv run pytest

check: lint fmt typecheck test

run:
	uv run uvicorn template.main:app --reload --port 8000

clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache
