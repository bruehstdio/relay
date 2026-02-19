# Relay

[![CI](https://github.com/bruehstdio/relay/actions/workflows/ci.yml/badge.svg)](https://github.com/bruehstdio/relay/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/bruehstdio/relay/branch/main/graph/badge.svg)](https://codecov.io/gh/bruehstdio/relay)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://bruehstdio.github.io/relay/)

**Chain AI coding agents like a CI pipeline.** Pass work from Claude Code → OpenCode → Aider (or any combination) with shared context and artifacts.

## Why Relay?

Different AI agents excel at different tasks:

- **Claude Code** — Great at understanding context, planning, and refactoring
- **OpenCode** — Fast, open-source, works with any provider
- **Aider** — Excellent at multi-file edits and git integration
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

## Quick Start

> **Note: PyPI package coming soon. Install from source for now.**

```bash
# Install Relay from source
git clone https://github.com/bruehstdio/relay.git
cd relay
pip install -e ".[dev]"

# Initialize a new project
mkdir my-project && cd my-project
relay init

# Run your pipeline
relay run
```

## Example Pipeline

```yaml
name: "feature-implementation"
description: "Plan, code, and review a new feature"

steps:
  - name: plan
    agent: claude-code
    prompt: |
      Analyze the codebase and create a detailed implementation plan.
      Output to plan.md.
    output: plan.md

  - name: implement
    agent: opencode
    prompt: |
      Based on plan.md, implement the feature following the approach.
    input: plan.md
    output: changes.diff

  - name: review
    agent: aider
    prompt: |
      Review the changes in changes.diff and suggest improvements.
    input: changes.diff
```

## Documentation

📚 **Full documentation is available at [bruehstdio.github.io/relay](https://bruehstdio.github.io/relay/)**

- **[Installation](https://bruehstdio.github.io/relay/installation/)** — Get Relay up and running
- **[Quick Start](https://bruehstdio.github.io/relay/quickstart/)** — Your first pipeline in 5 minutes
- **[Configuration](https://bruehstdio.github.io/relay/configuration/)** — Complete configuration reference
- **[CLI Reference](https://bruehstdio.github.io/relay/cli-reference/)** — All commands and options
- **[Examples](https://bruehstdio.github.io/relay/examples/)** — Real-world pipeline examples

## Installation

### Prerequisites

- Python 3.9 or higher
- At least one AI agent installed (Claude Code, OpenCode, Aider, or Codex)

<!-- ### Install from PyPI

> **Note: PyPI package coming soon.**

```bash
pip install relay-coder
```

### Install from Source -->

> **Note: PyPI package coming soon. Install from source for now.**

### Install from Source

```bash
git clone https://github.com/bruehstdio/relay.git
cd relay
pip install -e ".[dev]"
```

## Usage

```bash
# Initialize a new project
relay init

# Run the pipeline
relay run

# Preview what would run (dry run)
relay run --dry-run

# Monitor with dashboard
relay monitor

# List configured agents
relay list-agents
```

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Clone and setup
git clone https://github.com/bruehstdio/relay.git
cd relay
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install

# Run tests
pytest
```

## License

MIT License — see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with [Typer](https://typer.tiangolo.com/) for CLI
- Terminal UI powered by [Rich](https://rich.readthedocs.io/)
- Configuration with [Pydantic](https://docs.pydantic.dev/)
