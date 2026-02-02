# AGENTS.md — AI Agent Development Guide for Relay

**Project:** relay-coder — Chain AI coding agents like a CI pipeline  
**Repository:** https://github.com/danielfbmbot/relay  
**Maintainers:** Daniel (danielfbm) + AI assistants  
**Last Updated:** 2026-02-03

---

## 1. Project Overview

Relay is a Python CLI tool that chains AI coding agents (Claude Code, OpenCode, Aider, etc.) into pipelines with shared context and artifacts. Think of it as CI/CD for AI agents.

### Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   CLI       │────→│   Config    │────→│  Executor   │
│  (Typer)    │     │  (Pydantic) │     │(ThreadPool) │
└─────────────┘     └─────────────┘     └──────┬──────┘
       │                                        │
       ↓                                        ↓
┌─────────────┐                         ┌─────────────┐
│  Dashboard  │                         │   Agents    │
│  (Rich)     │                         │ (External)  │
└─────────────┘                         └─────────────┘
```

### Key Components

| File | Purpose |
|------|---------|
| `cli.py` | Typer CLI commands (run, init, list-agents, monitor) |
| `config.py` | YAML pipeline parsing and validation |
| `executor.py` | Pipeline execution engine with parallel step support |
| `models.py` | Pydantic models for configuration and results |
| `dashboard.py` | Rich terminal UI for monitoring |

---

## 2. Development Workflow

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/danielfbmbot/relay.git
cd relay

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Verify installation
relay --version
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=relay --cov-report=html

# Run specific test file
pytest tests/test_executor.py

# Run with verbose output
pytest -v
```

### Code Quality Checks

**Always run these before committing:**

```bash
# Linting (must pass 100 char line length)
ruff check src/

# Auto-fix linting issues where possible
ruff check --fix src/

# Type checking
mypy src/

# Format code
black src/

# Run full CI check locally
ruff check src/ && mypy src/ && pytest
```

### Making Changes

1. **Create a branch** for your changes
2. **Write tests** for new functionality
3. **Run quality checks** — all must pass
4. **Commit with clear messages** explaining why, not just what
5. **Push and create PR** — CI must pass before merge

---

## 3. Coding Standards

### Python Style

- **Line length:** 100 characters (enforced by ruff/black)
- **Type hints:** Required for all functions (enforced by mypy)
- **Docstrings:** Google style for all public functions
- **Imports:** Grouped as stdlib, third-party, local (enforced by ruff)

### Example Code Pattern

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


def process_step(
    step: StepConfig,
    agents: dict[str, AgentConfig],
    working_dir: Path | None = None,
) -> StepResult:
    """Process a single pipeline step.
    
    Args:
        step: Configuration for this step
        agents: Dictionary of available agent configurations
        working_dir: Optional working directory override
        
    Returns:
        StepResult with execution status and output
        
    Raises:
        AgentNotFoundError: If step.agent is not in agents dict
    """
    # Implementation here
    pass
```

### Linting Rules (ruff)

Selected rule sets:
- **E, F:** Pyflakes and pycodestyle errors
- **I:** Import sorting
- **N:** Naming conventions
- **W:** Warnings
- **UP:** Python upgrade checks

**Critical:** E501 (line too long) must be fixed — break into multiple lines.

---

## 4. Testing Requirements

### Test Structure

```
tests/
├── __init__.py
├── test_cli.py          # CLI command tests
├── test_config.py       # Configuration parsing tests
├── test_executor.py     # Pipeline execution tests
├── test_models.py       # Pydantic model validation tests
└── fixtures/
    ├── simple_pipeline.yml
    └── parallel_pipeline.yml
```

### Writing Tests

```python
import pytest
from relay.models import PipelineConfig, StepConfig


def test_pipeline_config_validation():
    """Test that pipeline config validates required fields."""
    config = PipelineConfig(
        name="test-pipeline",
        steps=[
            StepConfig(name="step1", agent="claude", prompt="test")
        ]
    )
    assert config.name == "test-pipeline"
    assert len(config.steps) == 1


def test_step_requires_agent_or_parallel():
    """Test that steps must have either agent or parallel defined."""
    with pytest.raises(ValueError):
        StepConfig(name="invalid", prompt="test")  # No agent or parallel
```

### Test Coverage Requirements

- **Minimum 80% coverage** for new code
- **100% coverage** for critical paths (executor, config parsing)
- Use `pytest-cov` to track coverage

---

## 5. Adding New Features

### Adding a New CLI Command

1. Edit `src/relay/cli.py`:

```python
@app.command()
def new_command(
    config: Path = typer.Option(..., "--config", "-c", help="Pipeline config file"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Description of what this command does."""
    console.print(f"Running new_command with {config}")
    # Implementation
```

2. Add tests in `tests/test_cli.py`
3. Update README.md with usage example

### Adding a New Agent Type

1. Update `src/relay/models.py` agent validation if needed
2. Add agent configuration example to README
3. Test with actual agent installation

### Adding Pipeline Features

Example: Adding retry logic

1. Add field to `StepConfig` in `models.py`:

```python
class StepConfig(BaseModel):
    # ... existing fields ...
    max_retries: int = Field(default=0, description="Number of retries on failure")
```

2. Implement in `executor.py`:

```python
def _execute_step_with_retry(self, step: StepConfig, ...) -> StepResult:
    for attempt in range(step.max_retries + 1):
        result = self._execute_step(...)
        if result.success or attempt == step.max_retries:
            return result
        console.print(f"Retry {attempt + 1}/{step.max_retries}...")
```

3. Add tests covering retry scenarios
4. Update example pipelines

---

## 6. CI/CD Pipeline

### GitHub Actions Workflow

**File:** `.github/workflows/ci.yml`

**Stages:**
1. **Test Matrix** — Python 3.9, 3.10, 3.11, 3.12, 3.13 on Ubuntu
2. **Linting** — ruff check
3. **Type Checking** — mypy
4. **Unit Tests** — pytest with coverage
5. **Build** — Package verification

### Required Checks (Must Pass)

- ✅ ruff linting
- ✅ mypy type checking
- ✅ pytest tests
- ✅ Build verification

### Troubleshooting CI Failures

Common issues:

1. **E501 Line too long** — Break into multiple lines
2. **F401 Unused import** — Remove or use `# noqa: F401`
3. **Type errors** — Add proper type hints
4. **Test failures** — Check test fixtures and mocks

---

## 7. Security Considerations

### Code Security

- **Never commit secrets** — Use environment variables
- **Validate all inputs** — Pydantic handles most, check edge cases
- **Sandbox agent execution** — Agents run in subprocess, validate commands
- **Audit logging** — Log all pipeline executions

### Safe Patterns

```python
# Good: Validate path before use
from pathlib import Path

def safe_read(path: Path) -> str:
    resolved = path.expanduser().resolve()
    # Prevent directory traversal
    if not str(resolved).startswith(str(Path.cwd())):
        raise ValueError("Path outside working directory")
    return resolved.read_text()

# Good: Use Pydantic for validation
class SafeConfig(BaseModel):
    command: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")  # Whitelist chars
```

---

## 8. Common Tasks

### Task: Fix Linting Errors

```bash
# See all errors
ruff check src/

# Auto-fix what can be fixed
ruff check --fix src/

# Fix remaining manually (usually line length)
# Break long lines into multiple shorter lines
```

### Task: Update Dependencies

```bash
# Edit pyproject.toml
# Update version constraints

# Test installation
pip install -e ".[dev]"

# Run full test suite
pytest
```

### Task: Add Parallel Step Support

Already implemented. See `executor.py` `_execute_parallel_step()` for reference.

### Task: Debug Test Failures

```bash
# Run single test with verbose output
pytest tests/test_executor.py::test_parallel_execution -v -s

# Run with debugger
pytest --pdb tests/test_executor.py

# Check coverage gaps
pytest --cov=relay --cov-report=term-missing
```

---

## 9. Release Process

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md** with changes
3. **Run full test suite** — all must pass
4. **Create git tag** — `git tag v0.2.0`
5. **Push tag** — `git push origin v0.2.0`
6. **GitHub Actions** — Builds and publishes to PyPI

---

## 10. Quick Reference

### Essential Commands

```bash
# Development setup
pip install -e ".[dev]"

# Quality checks (run before every commit)
ruff check src/ && mypy src/ && pytest

# Run CLI
relay run --config pipeline.yml
relay monitor

# Build package
python -m build
```

### Project Links

- **Issues:** https://github.com/danielfbmbot/relay/issues
- **CI Status:** https://github.com/danielfbmbot/relay/actions
- **Documentation:** README.md (this file)

### Getting Help

- Check existing issues on GitHub
- Review recent commits for patterns
- Ask Daniel (danielfbm) for context

---

## 11. AI Agent Instructions

When working on this codebase:

1. **Always run quality checks** before suggesting changes
2. **Write tests** for new functionality
3. **Keep line length ≤ 100** — break long lines
4. **Use type hints** for all functions
5. **Follow existing patterns** — consistency matters
6. **Commit frequently** with clear messages
7. **Check CI status** after pushing

**Before marking any task complete:**
- [ ] Code follows style guidelines (ruff passes)
- [ ] Type hints are correct (mypy passes)
- [ ] Tests pass (pytest passes)
- [ ] New features have tests
- [ ] Documentation is updated if needed

---

*This file should be kept up-to-date as the project evolves.*
