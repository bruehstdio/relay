# Relay

[![CI](https://github.com/danielfbmbot/relay/actions/workflows/ci.yml/badge.svg)](https://github.com/danielfbmbot/relay/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/danielfbmbot/relay/branch/main/graph/badge.svg)](https://codecov.io/gh/danielfbmbot/relay)

Chain AI coding agents like a CI pipeline. Pass work from Claude Code → OpenCode → Aider (or any combination) with shared context and artifacts.

## Why?

Different AI agents excel at different tasks:
- **Claude Code** — great at understanding context, planning, and refactoring
- **OpenCode** — fast, open-source, works with any provider
- **Aider** — excellent at multi-file edits and git integration

Instead of picking one, chain them together. Each agent gets the output of the previous one.

## Quick Start

```bash
pip install relay

# Run a pipeline
relay run --config pipeline.yml

# Launch the terminal dashboard
relay monitor

# Monitor a specific pipeline
relay monitor --config pipeline.yml
```

## Example Pipeline

```yaml
# pipeline.yml
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

## Supported Agents

- `claude-code` — Anthropic's Claude Code
- `opencode` — OpenCode CLI
- `aider` — Aider coding assistant
- `codex` — OpenAI Codex CLI
- Custom commands via `exec:`

## Configuration

```yaml
agents:
  claude-code:
    command: claude
    args: ["--verbose"]
  
  opencode:
    command: opencode
    env:
      OPENCODE_MODEL: claude-3-5-sonnet

pipelines:
  default:
    - plan
    - implement
    - review
```

## License

MIT
