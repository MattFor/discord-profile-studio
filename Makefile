.PHONY: install lint format typecheck test build clean

install:
	pip install -e ".[dev]"
	pre-commit install

lint:
	ruff check .

format:
	ruff format .

typecheck:
	basedpyright

test:
	pytest

build:
	python -m build

clean:
	rm -rf build dist .pytest_cache .ruff_cache htmlcov .coverage
