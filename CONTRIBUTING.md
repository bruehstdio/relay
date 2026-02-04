# Contributing to Relay

Thank you for your interest in contributing to Relay! This document provides guidelines for contributing to the project.

## Quick Start

1. **Fork and clone** the repository
2. **Set up development environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   pre-commit install
   ```
3. **Create a branch** for your changes
4. **Make your changes** following our coding standards
5. **Run quality checks** (see below)
6. **Submit a pull request**

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- Virtual environment tool (venv, virtualenv, or conda)

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/relay.git
cd relay

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in editable mode with all dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Verify installation
relay --version
```

## Code Quality Standards

All code must pass the following checks before being merged:

### Required Checks

Run these before every commit:

```bash
# Linting (auto-fix where possible)
ruff check --fix src/

# Type checking
mypy src/

# Run tests with coverage
pytest --cov=relay --cov-report=term-missing

# Full CI check
ruff check src/ && mypy src/ && pytest
```

### Style Guidelines

- **Line length:** 100 characters maximum
- **Type hints:** Required for all functions
- **Docstrings:** Google style for public functions
- **Imports:** Grouped as stdlib, third-party, local (enforced by ruff)

See `AGENTS.md` for detailed coding patterns and examples.

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=relay --cov-report=html

# Run specific test file
pytest tests/test_config.py

# Run with verbose output
pytest -v
```

### Writing Tests

- Write tests for all new functionality
- Maintain or improve test coverage (currently ~19%, target: 80%)
- Use pytest fixtures for shared test data
- Mock external dependencies (agents, file I/O)

## Pull Request Process

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes** with clear, focused commits

3. **Run quality checks** locally — all must pass

4. **Push your branch** and create a Pull Request

5. **Ensure CI passes** — GitHub Actions runs all checks

6. **Request review** from maintainers

### PR Checklist

Before submitting:

- [ ] Code follows style guidelines (ruff passes)
- [ ] Type hints are correct (mypy passes)
- [ ] Tests pass (pytest passes)
- [ ] New features have tests
- [ ] Documentation is updated if needed
- [ ] Commit messages are clear and descriptive

## Reporting Issues

### Bug Reports

Include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Python version and OS
- Error messages and stack traces

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternatives considered

## Development Workflow

### Branch Naming

- `feature/description` — New features
- `fix/description` — Bug fixes
- `docs/description` — Documentation updates
- `refactor/description` — Code refactoring

### Commit Messages

Write clear, descriptive commit messages:

```
Add parallel step execution support

- Implement ThreadPoolExecutor for parallel steps
- Add max_workers configuration option
- Update tests for concurrent execution
```

## Project Structure

```
relay/
├── src/relay/          # Main source code
│   ├── cli.py          # CLI commands
│   ├── config.py       # Configuration parsing
│   ├── executor.py     # Pipeline execution
│   ├── models.py       # Pydantic models
│   └── dashboard.py    # Terminal UI
├── tests/              # Test suite
├── examples/           # Example pipelines
├── .github/workflows/  # CI configuration
├── pyproject.toml      # Project configuration
└── README.md           # User documentation
```

## Questions?

- Check existing [issues](https://github.com/danielfbmbot/relay/issues)
- Review `AGENTS.md` for detailed development patterns
- Ask in your pull request or issue

## License

By contributing to Relay, you agree that your contributions will be licensed under the MIT License.
