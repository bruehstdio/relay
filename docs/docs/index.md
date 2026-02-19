# Relay

[![CI](https://github.com/bruehstdio/relay/actions/workflows/ci.yml/badge.svg)](https://github.com/bruehstdio/relay/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/bruehstdio/relay/branch/main/graph/badge.svg)](https://codecov.io/gh/bruehstdio/relay)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

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

## Next Steps

- **[Installation](installation.md)** — Get Relay up and running
- **[Quick Start](quickstart.md)** — Your first pipeline
- **[Configuration](configuration.md)** — Learn how to configure Relay
- **[API Reference](api/index.md)** — Explore the Python API

## License

MIT License — see [LICENSE](https://github.com/bruehstdio/relay/blob/main/LICENSE) for details.
