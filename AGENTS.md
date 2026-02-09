# AGENTS.md - Relay

## Repository Overview

**Name:** Relay  
**Type:** CLI Tool - AI Agent Pipeline Orchestrator  
**Language:** Python 3.9+  
**Framework:** Typer + Rich  
**Primary Focus:** Chain AI coding agents like CI/CD pipelines

## Quick Links

- **Issues:** https://codeberg.org/daniel-org/relay/issues
- **Docs:** ./docs/
- **Source:** `src/relay/`
- **Tests:** `tests/`

## Architecture

```
relay/
├── src/relay/
│   ├── __init__.py
│   ├── cli.py              # Main CLI entry point
│   ├── config.py           # Configuration management
│   ├── models.py           # Pydantic models
│   ├── executor.py         # Pipeline execution engine
│   ├── output_formatter.py # Rich terminal output
│   ├── conditions.py       # Conditional step logic
│   └── cache.py            # Artifact caching
├── tests/
├── examples/               # Sample pipelines
└── pipeline.yml            # Example config
```

## Engineering Best Practices

### Code Style
- **Python:** PEP 8 compliant
- **Type Hints:** All functions typed
- **Docstrings:** Google style
- **Commits:** Conventional commits
- **Branches:** `feature/issue-#`, `fix/issue-#`

### Worktree Branching Strategy

```bash
# 1. Setup
cd ~/code/codeberg.org/daniel-org/relay
git fetch origin

# 2. Create worktree
BRANCH="feature/issue-$(date +%s)"
git worktree add ../worktrees/relay-$BRANCH -b $BRANCH
cd ../worktrees/relay-$BRANCH

# 3. Create virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 4. Work, test, commit
# ... coding ...
pytest
ruff check .
mypy src/

# 5. Push and PR
git push origin $BRANCH
# Create PR via API

# 6. Cleanup after merge
cd ~/code/codeberg.org/daniel-org/relay
git worktree remove ../worktrees/relay-$BRANCH
git branch -d $BRANCH
```

### Testing Requirements

**Before ANY commit:**
```bash
# Linting
ruff check .
ruff format --check

# Type checking
mypy src/

# Tests
pytest

# Coverage (aim for 70%+)
pytest --cov=src/relay --cov-report=term-missing
```

### Design Document Template

For features > 1 day, create `docs/designs/FEATURE-###-short-name.md`:

```markdown
# Feature Design: [Name]

## Issue Reference
Fixes #[issue-number]

## Overview
Brief description

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## Technical Design

### CLI Changes
```python
# New commands or flags
```

### Core Changes
```python
# New classes or functions
```

### Configuration Changes
```yaml
# New pipeline.yml options
```

## Test Plan

### Unit Tests
- [ ] Test case 1
- [ ] Test case 2

### Integration Tests
- [ ] CLI scenario 1
- [ ] Pipeline execution test

## Implementation Steps
1. Step 1
2. Step 2
3. Step 3

## Documentation Updates
- [ ] README.md
- [ ] CLI help text
- [ ] Example pipelines
```

## Development Workflow

### 1. Pick Issue
```bash
curl -H "Authorization: token $CODEBERG_TOKEN" \
  "https://codeberg.org/api/v1/repos/daniel-org/relay/issues?labels=priority-high,status-todo"
```

### 2. Update Status
```bash
curl -X POST -H "Authorization: token $CODEBERG_TOKEN" \
  "https://codeberg.org/api/v1/repos/daniel-org/relay/issues/[number]/labels" \
  -d '{"labels":["status-in-progress"]}'
```

### 3. Create Design Doc (if > 1 day effort)

### 4. Implement with TDD
```bash
# Write test first
# Then implementation
# Then verify
pytest tests/test_[feature].py -v
```

### 5. Full Test Suite
```bash
# Run all checks
just check  # or: ruff check . && mypy src/ && pytest
```

### 6. Commit
```bash
git commit -m "feat: description - fixes #[number]

- Change 1
- Change 2

Test plan:
- [x] Unit tests added
- [x] Integration tests pass
- [x] Type checking passes
- [x] Linting clean"
```

### 7. Create PR
```bash
git push origin [branch-name]

# Create PR
curl -X POST -H "Authorization: token $CODEBERG_TOKEN" \
  "https://codeberg.org/api/v1/repos/daniel-org/relay/pulls" \
  -d '{
    "title": "feat: description - fixes #[number]",
    "body": "## Summary\n...\n\n## Testing\n- [x] Tests pass\n- [x] Coverage maintained\n- [x] Type check clean\n\nFixes #[number]",
    "head": "[branch-name]",
    "base": "main"
  }'
```

## Current Priority Issues

1. **#8:** Increase test coverage to 70% → 3-5 days
2. **#9:** Create documentation site → 2-3 days
3. **#10:** Publish to PyPI → 1 day

## Common Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run CLI
relay --help
relay run pipeline.yml
relay monitor

# Testing
pytest
pytest -xvs tests/test_specific.py
pytest --cov=src/relay --cov-report=html

# Linting
ruff check .
ruff check --fix .
ruff format .

# Type checking
mypy src/

# Using Just
just check      # Run all checks
just test       # Run tests
just lint       # Run linter
just format     # Format code
```

## Pipeline Configuration Format

```yaml
# pipeline.yml
name: Example Pipeline

steps:
  - name: analyze
    agent: claude
    prompt: Analyze the codebase for issues
    
  - name: fix
    agent: aider
    prompt: Fix the identified issues
    depends_on: [analyze]
    
  - name: test
    command: pytest
    depends_on: [fix]
```

## Agent Integration

Supported agents:
- `claude` - Claude Code
- `aider` - Aider coding assistant
- `codex` - OpenAI Codex CLI
- `gemini` - Gemini CLI

Adding new agents:
1. Add to `src/relay/models.py`
2. Implement in `src/relay/executor.py`
3. Add tests
4. Update README

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag: `git tag v0.x.x`
4. Push tag: `git push origin v0.x.x`
5. CI publishes to PyPI automatically

## Troubleshooting

**Import errors:**
```bash
pip install -e ".[dev]"
```

**Test failures:**
```bash
# Run specific test
pytest tests/test_file.py::test_function -xvs
```

**Type errors:**
```bash
mypy src/ --show-error-codes
```

## Performance Considerations

- Pipeline steps run in isolated processes
- Artifact caching reduces redundant work
- Parallel execution for independent steps
- Progress displayed via Rich library

## Contact

For questions, contact Daniel via Telegram.

---

*Last updated: February 8, 2026*
