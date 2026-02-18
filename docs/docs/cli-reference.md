# CLI Reference

Complete reference for the Relay command-line interface.

## Global Options

All Relay commands support these global options:

| Option | Description |
|--------|-------------|
| `--help` | Show help message and exit |
| `--version` | Show version information |
| `--install-completion` | Install shell completion (bash, zsh, fish) |

## Commands

### `relay run`

Execute a pipeline.

```bash
relay run [OPTIONS]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--config` | `-c` | Pipeline configuration file | `pipeline.yml` (auto-detected) |
| `--working-dir` | `-w` | Working directory | Current directory |
| `--dry-run` | `-n` | Preview what would be executed without running | `false` |
| `--format` | `-f` | Output format: `console`, `json`, `yaml` | `console` |
| `--output` | `-o` | Output file path | stdout |
| `--log-level` | `-l` | Log level: `debug`, `info`, `warning`, `error` | `info` |
| `--log-format` | | Log format: `console`, `json` | `console` |

**Examples:**

```bash
# Run default pipeline
relay run

# Run specific pipeline file
relay run --config my-pipeline.yml

# Preview execution (dry run)
relay run --dry-run

# Run in different directory
relay run --working-dir ./my-project

# Output results as JSON
relay run --format json --output results.json

# Run with debug logging
relay run --log-level debug
```

**Exit Codes:**

| Code | Meaning |
|------|---------|
| `0` | All steps succeeded |
| `1` | One or more steps failed |

---

### `relay init`

Initialize a new Relay project with example configuration files.

```bash
relay init [NAME] [OPTIONS]
```

**Arguments:**

| Argument | Description | Default |
|----------|-------------|---------|
| `NAME` | Project name | `my-pipeline` |

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--template` | `-t` | Template to use (e.g., `python-project`) | None |

**Examples:**

```bash
# Initialize with default settings
relay init

# Initialize with specific name
relay init my-awesome-project

# Initialize from template
relay init my-project --template python-project
```

**Created Files:**

- `relay.yml` — Global configuration with agent definitions
- `pipeline.yml` — Pipeline definition

---

### `relay list-agents`

Display all configured agents from `relay.yml`.

```bash
relay list-agents
```

**Example Output:**

```
┏━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Name        ┃ Command ┃ Args                ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ claude-code │ claude  │ --verbose           │
│ opencode    │ opencode│                     │
│ aider       │ aider   │ --no-git --stream   │
└─────────────┴─────────┴─────────────────────┘
```

---

### `relay monitor`

Launch the terminal dashboard for monitoring pipelines.

```bash
relay monitor [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--config` | `-c` | Pipeline to monitor (optional) |
| `--working-dir` | `-w` | Working directory |

**Examples:**

```bash
# Launch general dashboard
relay monitor

# Monitor specific pipeline
relay monitor --config my-pipeline.yml
```

---

### `relay visualize`

Visualize pipeline dependencies as a DAG (Directed Acyclic Graph).

```bash
relay visualize [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--config` | `-c` | Pipeline configuration file |

**Status:** 🚧 Not yet implemented

---

## Template Commands

### `relay template list`

List all available templates.

```bash
relay template list
```

**Example Output:**

```
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name            ┃ Version ┃ Source  ┃ Description                            ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ python-project  │ 1.0.0   │ builtin │ Python project with linting and testing│
│ web-project     │ 1.0.0   │ builtin │ Web development template               │
│ docs-project    │ 1.0.0   │ builtin │ Documentation improvement pipeline     │
└─────────────────┴─────────┴─────────┴────────────────────────────────────────┘
```

---

### `relay template show`

Display detailed information about a template.

```bash
relay template show <NAME>
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `NAME` | Template name with optional version (e.g., `python-project@1.0.0`) |

**Examples:**

```bash
# Show latest version
relay template show python-project

# Show specific version
relay template show python-project@1.0.0
```

---

### `relay template install`

Install built-in templates to the user directory (`~/.relay/templates/`).

```bash
relay template install
```

This copies all built-in templates to your user directory, where you can customize them.

---

## Cache Commands

### `relay cache list`

List all cached artifacts.

```bash
relay cache list [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--working-dir` | `-w` | Working directory |

**Example Output:**

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Key                         ┃ Size   ┃ Created     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━┩
│ plan.md-step-1-a1b2c3d4     │ 2.3 KB │ 2024-01-15  │
│ code.py-step-2-e5f6g7h8     │ 5.1 KB │ 2024-01-15  │
└─────────────────────────────┴────────┴─────────────┘
```

---

### `relay cache clear`

Clear all cached artifacts.

```bash
relay cache clear [OPTIONS]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--working-dir` | `-w` | Working directory |
| `--yes` | `-y` | Skip confirmation prompt |

**Examples:**

```bash
# Clear with confirmation
relay cache clear

# Clear without confirmation
relay cache clear --yes
```

---

## Shell Completion

Relay supports shell completion for Bash, Zsh, and Fish.

### Install Completion

```bash
# Bash
relay --install-completion bash

# Zsh
relay --install-completion zsh

# Fish
relay --install-completion fish
```

After installation, restart your shell or source your shell configuration file.

---

## Environment Variables

Relay recognizes these environment variables:

| Variable | Description |
|----------|-------------|
| `RELAY_CONFIG` | Path to global config file (overrides auto-detection) |
| `RELAY_CACHE_DIR` | Cache directory path |
| `RELAY_LOG_LEVEL` | Default log level |

---

## Troubleshooting

### Command not found

If `relay` is not found after installation:

```bash
# Check if pip bin directory is in PATH
which relay

# Or run with python module
python -m relay.cli
```

### Pipeline not found

If Relay can't find your pipeline:

```bash
# Explicitly specify the config file
relay run --config ./path/to/pipeline.yml

# Check working directory
relay run --working-dir ./my-project
```

### Agent not found

If an agent is not found:

```bash
# List configured agents
relay list-agents

# Check that the agent is installed and in PATH
which claude
which opencode
```
