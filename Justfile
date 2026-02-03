# Justfile for relay project
# Install just: https://github.com/casey/just

# Default recipe - show available commands
default:
    @just --list

# Run all checks (lint, type-check, test)
check:
    ruff check src/
    mypy src/
    pytest

# Fix auto-fixable linting issues
fix:
    ruff check --fix src/

# Run tests with coverage
test:
    pytest --cov=relay --cov-report=term-missing

# Run only fast tests (no integration)
test-fast:
    pytest -m "not integration"

# Type check only
types:
    mypy src/

# Lint only
lint:
    ruff check src/

# Format code
format:
    ruff format src/

# Install dev dependencies and pre-commit hooks
install:
    pip install -e ".[dev]"
    pre-commit install

# Run pre-commit on all files
clean:
    pre-commit run --all-files

# Build package
build:
    python -m build

# Clean build artifacts
distclean:
    rm -rf dist/ build/ *.egg-info/

# Run relay in development mode
dev *ARGS:
    python -m relay {{ARGS}}
