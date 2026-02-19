# Contributing

Thank you for your interest in contributing to Relay!

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/bruehstdio/relay.git
cd relay
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -e ".[dev]"
```

### 4. Install Pre-commit Hooks

```bash
pre-commit install
```

## Project Structure

```
relay/
├── src/relay/           # Source code
│   ├── __init__.py
│   ├── cli.py           # CLI interface
│   ├── models.py        # Pydantic models
│   ├── executor.py      # Pipeline execution
│   ├── config.py        # Config loading
│   ├── cache.py         # Caching system
│   ├── templates.py     # Template management
│   ├── dashboard.py     # Terminal UI
│   └── data/            # Built-in templates
├── tests/               # Test suite
├── docs/                # Documentation
└── pyproject.toml       # Project configuration
```

## Running Tests

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

## Code Quality

### Linting

```bash
# Run ruff
ruff check src/

# Auto-fix issues
ruff check src/ --fix
```

### Type Checking

```bash
mypy src/
```

### Formatting

```bash
# Format code
black src/

# Check formatting
black src/ --check
```

## Adding New Features

### Adding a CLI Command

1. Add command function in `src/relay/cli.py`:

```python
@app.command()
def my_command(
    arg: Annotated[str, typer.Argument(help="Argument description")],
) -> None:
    """Command description."""
    console.print(f"Hello, {arg}!")
```

2. Add tests in `tests/test_cli.py`

3. Update documentation

### Adding a New Model

1. Add model in `src/relay/models.py`:

```python
class MyNewConfig(BaseModel):
    """Description of the config."""
    
    field: str = Field(description="Field description")
```

2. Add validation if needed using `@field_validator`

3. Update tests and documentation

### Adding a Template

1. Create template file in `src/relay/data/templates/`:

```yaml
# my-template@1.0.0.yml
name: "my-template"
description: "Description"
steps:
  - name: step1
    agent: claude-code
    prompt: "Do something"
```

2. Test with: `relay template list`

## Writing Tests

### Test Structure

```python
# tests/test_feature.py
import pytest
from relay.models import AgentConfig, StepConfig

class TestFeature:
    """Test feature description."""
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        config = AgentConfig(command="test")
        assert config.command == "test"
    
    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            # Code that raises error
            pass
```

### Using Fixtures

```python
@pytest.fixture
def sample_config():
    return AgentConfig(
        command="claude",
        args=["--verbose"],
        timeout=300
    )

def test_with_fixture(sample_config):
    assert sample_config.timeout == 300
```

## Documentation

### Updating Docs

1. Edit files in `docs/docs/`
2. Test locally:

```bash
cd docs
mkdocs serve
```

3. View at http://localhost:8000

### Docstring Style

Use Google-style docstrings:

```python
def my_function(arg1: str, arg2: int) -> bool:
    """Short description.
    
    Longer description if needed.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When something is wrong
    """
    return True
```

## Submitting Changes

### 1. Create a Branch

```bash
git checkout -b feature/my-feature
```

### 2. Make Changes

- Write code
- Add tests
- Update documentation

### 3. Run Quality Checks

```bash
pytest
ruff check src/
mypy src/
black src/ --check
```

### 4. Commit

```bash
git add .
git commit -m "feat: add new feature"
```

Follow conventional commits:

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation
- `test:` — Tests
- `refactor:` — Code refactoring
- `chore:` — Maintenance

### 5. Push and Create PR

```bash
git push origin feature/my-feature
```

Then create a Pull Request on GitHub.

## Code Style

- **Line length:** 100 characters
- **Python version:** 3.9+
- **Type hints:** Required for all functions
- **Docstrings:** Required for all public functions/classes

## Getting Help

- Open an issue for bugs or feature requests
- Join discussions for questions
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
