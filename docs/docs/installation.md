# Installation

## Requirements

- Python 3.9 or higher
- At least one AI agent installed (Claude Code, OpenCode, Aider, or Codex)

## Install from PyPI

```bash
pip install relay-coder
```

## Install from Source

```bash
git clone https://github.com/danielfbmbot/relay.git
cd relay
pip install -e ".[dev]"
```

## Verify Installation

```bash
# Check version
relay --version

# Show help
relay --help
```

## Installing AI Agents

Relay works with any command-line AI agent. Here are installation instructions for popular options:

### Claude Code

```bash
# Via npm
npm install -g @anthropic-ai/claude-code

# Or follow official instructions at:
# https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview
```

### OpenCode

```bash
# Via npm
npm install -g opencode

# Or via the web app at:
# https://opencode.ai
```

### Aider

```bash
# Via pip
pip install aider-chat

# Or via pipx
pipx install aider-chat
```

### Codex

```bash
# Via npm (OpenAI's CLI)
npm install -g @openai/codex
```

## Shell Completion

Relay supports shell completion for Bash, Zsh, and Fish:

```bash
# Bash
relay --install-completion bash

# Zsh
relay --install-completion zsh

# Fish
relay --install-completion fish
```

## Next Steps

Now that you have Relay installed, head over to the [Quick Start](quickstart.md) guide to create your first pipeline.
