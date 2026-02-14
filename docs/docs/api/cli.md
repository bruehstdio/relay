# CLI API

The `relay.cli` module provides the command-line interface.

## Module Reference

::: relay.cli
    options:
      show_source: true
      show_root_heading: true

## Commands

### `relay run`

Execute a pipeline.

```python
from relay.cli import app
from typer.testing import CliRunner

runner = CliRunner()
result = runner.invoke(app, ["run", "--config", "pipeline.yml"])
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--config` | `-c` | Pipeline configuration file |
| `--working-dir` | `-w` | Working directory |
| `--dry-run` | `-n` | Show what would be executed |
| `--format` | `-f` | Output format: `console`, `json` |
| `--output` | `-o` | Output file path |
| `--log-level` | `-l` | Log level: `debug`, `info`, `warning`, `error` |

### `relay init`

Initialize a new project.

```python
result = runner.invoke(app, ["init", "my-project", "--template", "python-project"])
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `name` | Project name |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--template` | `-t` | Template to use |

### `relay list-agents`

List configured agents.

```python
result = runner.invoke(app, ["list-agents"])
```

### `relay monitor`

Launch terminal dashboard.

```python
result = runner.invoke(app, ["monitor"])
```

### `relay template list`

List available templates.

```python
result = runner.invoke(app, ["template", "list"])
```

### `relay template show`

Show template details.

```python
result = runner.invoke(app, ["template", "show", "python-project"])
```

### `relay template install`

Install built-in templates.

```python
result = runner.invoke(app, ["template", "install"])
```

### `relay cache list`

List cached artifacts.

```python
result = runner.invoke(app, ["cache", "list"])
```

### `relay cache clear`

Clear cached artifacts.

```python
result = runner.invoke(app, ["cache", "clear", "--yes"])
```

## Programmatic Usage

```python
from relay.cli import app
from typer.testing import CliRunner

runner = CliRunner()

# Run a pipeline
result = runner.invoke(app, [
    "run",
    "--config", "pipeline.yml",
    "--working-dir", "/path/to/project",
    "--dry-run"
])

assert result.exit_code == 0
print(result.output)
```
