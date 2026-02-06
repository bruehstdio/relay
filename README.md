# Relay

[![CI](https://github.com/danielfbmbot/relay/actions/workflows/ci.yml/badge.svg)](https://github.com/danielfbmbot/relay/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/danielfbmbot/relay/branch/main/graph/badge.svg)](https://codecov.io/gh/danielfbmbot/relay)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Chain AI coding agents like a CI pipeline. Pass work from Claude Code → OpenCode → Aider (or any combination) with shared context and artifacts.

## Why?

Different AI agents excel at different tasks:
- **Claude Code** — great at understanding context, planning, and refactoring
- **OpenCode** — fast, open-source, works with any provider
- **Aider** — excellent at multi-file edits and git integration
- **Codex** — OpenAI's coding assistant

Instead of picking one, chain them together. Each agent gets the output of the previous one.

## Features

- **Multi-Agent Pipelines** — Chain multiple AI agents together
- **Artifact Passing** — Share outputs between steps automatically
- **Parallel Execution** — Run multiple agents simultaneously
- **Conditional Steps** — Execute steps based on conditions
- **Environment Variables** — Configurable per-agent and per-step
- **Rich Dashboard** — Terminal UI for monitoring pipelines
- **Flexible Configuration** — YAML-based configuration with env var interpolation

## Installation

### Prerequisites

- Python 3.9 or higher
- At least one AI agent installed (Claude Code, OpenCode, Aider, or Codex)

### Install from PyPI

```bash
pip install relay-coder
```

### Install from Source

```bash
git clone https://github.com/danielfbmbot/relay.git
cd relay
pip install -e ".[dev]"
```

### Verify Installation

```bash
relay --version
relay --help
```

## Quick Start

### 1. Initialize a New Project

```bash
mkdir my-project
cd my-project
relay init
```

This creates:
- `relay.yml` — Global configuration with agent definitions
- `pipeline.yml` — Your pipeline definition

### 2. Configure Your Agents

Edit `relay.yml` to configure your agents:

```yaml
agents:
  claude-code:
    command: claude
    args: ["--verbose"]
  
  opencode:
    command: opencode
    env:
      OPENCODE_MODEL: claude-3-5-sonnet
  
  aider:
    command: aider
    args: ["--no-git"]
```

### 3. Define Your Pipeline

Edit `pipeline.yml` to define your workflow:

```yaml
name: "feature-implementation"
description: "Plan, code, and review a new feature"

steps:
  - name: plan
    agent: claude-code
    prompt: |
      Analyze the codebase and create a detailed implementation plan
      for adding user authentication. Output to plan.md.
    output: plan.md

  - name: implement
    agent: opencode
    prompt: |
      Based on the plan in plan.md, implement the authentication
      feature following the outlined approach.
    input: plan.md
    output: changes.diff

  - name: review
    agent: aider
    prompt: |
      Review the changes in changes.diff. Suggest improvements
      and fix any issues you find.
    input: changes.diff
```

### 4. Run the Pipeline

```bash
# Run the pipeline
relay run

# Or specify a config file
relay run --config pipeline.yml

# Dry run to preview what would execute
relay run --dry-run

# Monitor with the dashboard
relay monitor
```

## Configuration Reference

### Global Configuration (`relay.yml`)

```yaml
# Define your agents
agents:
  agent-name:
    command: command-to-run      # Required: The command to invoke
    args: ["--flag", "value"]   # Optional: Default arguments
    env:                         # Optional: Environment variables
      KEY: value
    timeout: 300                 # Optional: Timeout in seconds (default: 300)

# Define named pipelines
pipelines:
  default:
    - step1
    - step2
    - step3
  
  quick:
    - analyze
    - fix
```

### Pipeline Configuration (`pipeline.yml`)

```yaml
name: "pipeline-name"           # Required: Pipeline name
description: "Description"      # Optional: Pipeline description

steps:                          # Required: List of steps
  - name: step-name             # Required: Unique step name
    agent: agent-name           # Required: Agent to use (unless parallel)
    prompt: |                   # Optional: Prompt/instructions
      Instructions for the agent
    input: previous-output.txt  # Optional: Input file from artifacts
    output: result.txt          # Optional: Output file to save
    working_dir: ./subdir       # Optional: Working directory for step
    continue_on_error: false    # Optional: Continue pipeline on error
    timeout: 600                # Optional: Step timeout (e.g., '10m', '60s')
    if: "env.RUN_STEP == 'true'" # Optional: Condition to run step
    
    # Parallel execution
    parallel:                   # Optional: Run sub-steps in parallel
      - name: sub-step-1
        agent: agent-1
        prompt: "Task 1"
        output: result1.txt
      - name: sub-step-2
        agent: agent-2
        prompt: "Task 2"
        output: result2.txt
    parallel_strategy: concat   # Optional: concat, json, or first
```

### Environment Variable Interpolation

Both config files support environment variable interpolation:

```yaml
name: "Pipeline for ${PROJECT_NAME}"
steps:
  - name: deploy
    agent: ${DEPLOY_AGENT:-claude-code}
    prompt: "Deploy to ${ENVIRONMENT}"
```

Supports:
- `${VAR}` — Simple substitution
- `${VAR:-default}` — Substitution with default value

## Supported Agents

Relay works with any command-line AI agent:

| Agent | Command | Notes |
|-------|---------|-------|
| Claude Code | `claude` | Anthropic's Claude Code |
| OpenCode | `opencode` | Open-source, any provider |
| Aider | `aider` | Excellent multi-file edits |
| Codex | `codex` | OpenAI's coding assistant |
| Custom | Any | Use `exec:` prefix for custom commands |

### Custom Commands

Use any command as an agent:

```yaml
agents:
  custom-script:
    command: python
    args: ["my_script.py"]
    env:
      API_KEY: ${MY_API_KEY}
```

## Advanced Features

### Parallel Execution

Run multiple agents simultaneously:

```yaml
steps:
  - name: code-review
    parallel:
      - name: security-check
        agent: claude-code
        prompt: "Check for security issues"
        output: security.txt
      
      - name: performance-check
        agent: opencode
        prompt: "Check for performance issues"
        output: performance.txt
      
      - name: style-check
        agent: claude-code
        prompt: "Check code style"
        output: style.txt
    
    parallel_strategy: concat    # Options: concat, json, first
    output: review-results.txt
```

Parallel strategies:
- `concat` — Concatenate all outputs (default)
- `json` — Merge as JSON object
- `first` — Use first successful output

### Conditional Steps

Execute steps based on conditions:

```yaml
steps:
  - name: deploy
    agent: claude-code
    prompt: "Deploy to production"
    if: "env.DEPLOY_ENV == 'production'"
  
  - name: notify
    agent: claude-code
    prompt: "Send notification"
    if: "steps.deploy.success"
```

Condition types:
- `env.VAR == 'value'` — Environment variable comparison
- `env.VAR` — Environment variable exists
- `file.exists('path')` — File exists
- `steps.step_name.success` — Previous step succeeded
- `steps.step_name.failed` — Previous step failed
- `steps.step_name.exit_code == 0` — Exit code comparison
- `always` — Always run
- `never` — Never run

### Retry Configuration

Configure retry behavior for flaky agents:

```yaml
steps:
  - name: unreliable-step
    agent: opencode
    prompt: "Do something"
    retry:
      max_attempts: 3
      backoff: exponential        # or 'linear'
      delay: 5s
      max_delay: 60s
```

### Working Directory

Run steps in different directories:

```yaml
steps:
  - name: backend-tests
    agent: claude-code
    prompt: "Run backend tests"
    working_dir: ./backend
  
  - name: frontend-tests
    agent: claude-code
    prompt: "Run frontend tests"
    working_dir: ./frontend
```

## CLI Reference

### Commands

| Command | Description |
|---------|-------------|
| `relay run` | Execute a pipeline |
| `relay init [name]` | Initialize a new project |
| `relay list-agents` | Show configured agents |
| `relay monitor` | Launch terminal dashboard |

### Global Options

| Option | Description |
|--------|-------------|
| `--config, -c` | Pipeline configuration file |
| `--working-dir, -w` | Working directory |
| `--dry-run, -n` | Preview what would execute |
| `--help` | Show help |

### Examples

```bash
# Run default pipeline
relay run

# Run specific pipeline
relay run --config my-pipeline.yml

# Preview execution
relay run --dry-run

# Run in different directory
relay run --working-dir ./my-project

# Initialize project
relay init my-awesome-project

# List configured agents
relay list-agents

# Launch dashboard
relay monitor
```

## Examples

### Code Review Pipeline

```yaml
name: "automated-review"
steps:
  - name: analyze
    parallel:
      - name: security
        agent: claude-code
        prompt: "Review for security issues"
        output: security.md
      - name: performance
        agent: opencode
        prompt: "Review for performance issues"
        output: performance.md
    parallel_strategy: concat
    output: analysis.md
  
  - name: summarize
    agent: claude-code
    prompt: "Summarize findings"
    input: analysis.md
    output: summary.md
```

### Deployment Pipeline

```yaml
name: "deploy"
steps:
  - name: test
    agent: opencode
    prompt: "Run all tests"
    if: "env.RUN_TESTS != 'false'"
  
  - name: build
    agent: claude-code
    prompt: "Build the project"
  
  - name: deploy
    agent: claude-code
    prompt: "Deploy to ${ENVIRONMENT:-staging}"
    if: "steps.build.success"
```

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Quick start for contributors:

```bash
# Clone and setup
git clone https://github.com/danielfbmbot/relay.git
cd relay
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install

# Run tests
pytest

# Run linting
ruff check src/
mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with [Typer](https://typer.tiangolo.com/) for CLI
- Terminal UI powered by [Rich](https://rich.readthedocs.io/)
- Configuration with [Pydantic](https://docs.pydantic.dev/)
