# Agents

Agents are the AI tools that execute pipeline steps. Relay can work with any command-line AI agent.

## Built-in Agents

Relay comes with pre-configured defaults:

| Agent Name | Command | Description |
|------------|---------|-------------|
| `claude-code` | `claude` | Anthropic's Claude Code |
| `opencode` | `opencode` | Open-source coding assistant |
| `opencode-run` | `opencode run` | OpenCode in run mode |
| `oh-my-opencode` | `oh-my-opencode` | OMO wrapper for OpenCode |
| `gemini` | `gemini` | Google's Gemini CLI |
| `aider` | `aider` | Multi-file editing |
| `codex` | `codex` | OpenAI's Codex CLI |

These agents are automatically available without configuration.

## Custom Agents

Define your own agents in `relay.yml`:

```yaml
agents:
  my-custom-agent:
    command: python
    args: ["my_agent.py"]
    env:
      API_KEY: ${MY_API_KEY}
      MODEL: gpt-4
    timeout: 600
```

## Agent Configuration Reference

### Command

The command to execute:

```yaml
agents:
  claude-code:
    command: claude
  
  custom-script:
    command: /path/to/my/script.sh
```

### Arguments

Default arguments passed to the command:

```yaml
agents:
  claude-verbose:
    command: claude
    args: ["--verbose", "--output-format=json"]
  
  aider-no-git:
    command: aider
    args: ["--no-git", "--stream"]
```

### Environment Variables

Set environment variables for the agent:

```yaml
agents:
  opencode-custom:
    command: opencode
    env:
      OPENCODE_MODEL: claude-3-5-sonnet
      OPENCODE_TEMPERATURE: "0.7"
      PATH: "/usr/local/bin:/usr/bin:/bin"
```

### Timeout

Set a custom timeout (in seconds):

```yaml
agents:
  slow-agent:
    command: claude
    timeout: 900  # 15 minutes
  
  fast-agent:
    command: opencode
    timeout: 60   # 1 minute
```

## Agent Selection Strategies

### Per-Step Agent

Different steps can use different agents:

```yaml
steps:
  - name: plan
    agent: claude-code      # Good at planning
    prompt: "Create a plan"

  - name: implement
    agent: opencode         # Fast execution
    prompt: "Implement the plan"

  - name: review
    agent: aider            # Good at multi-file edits
    prompt: "Review the code"
```

### Environment-Based Selection

Use environment variables to select agents:

```yaml
agents:
  primary:
    command: ${PRIMARY_AGENT_COMMAND:-claude}
  
  fallback:
    command: ${FALLBACK_AGENT_COMMAND:-opencode}

steps:
  - name: task
    agent: primary
    prompt: "Do something"
```

## Popular AI Agents

### Claude Code

```yaml
agents:
  claude-code:
    command: claude
    args: ["--verbose"]
    env:
      CLAUDE_CODE_DEBUG: "1"
    timeout: 600
```

**Best for:** Planning, refactoring, complex reasoning

### OpenCode

```yaml
agents:
  opencode:
    command: opencode
    env:
      OPENCODE_MODEL: claude-3-5-sonnet
      OPENCODE_API_KEY: ${OPENCODE_API_KEY}
    timeout: 300
  
  opencode-run:
    command: opencode
    args: ["run"]
    timeout: 300
```

**Best for:** Fast execution, any provider, cost-effective

### Aider

```yaml
agents:
  aider:
    command: aider
    args: ["--no-git", "--stream"]
    timeout: 900
  
  aider-commit:
    command: aider
    args: ["--commit"]
    timeout: 900
```

**Best for:** Multi-file edits, git integration

### Codex

```yaml
agents:
  codex:
    command: codex
    env:
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    timeout: 300
```

**Best for:** OpenAI models, familiar interface

## Creating Custom Agents

Any command-line tool can be a Relay agent. The tool should:

1. Accept input via stdin
2. Produce output via stdout
3. Return exit code 0 on success, non-zero on failure

### Example: Python Script Agent

```python
#!/usr/bin/env python3
# my_agent.py
import sys

# Read prompt from stdin
prompt = sys.stdin.read()

# Process...
result = f"Processed: {prompt[:50]}..."

# Write to stdout
print(result)
```

```yaml
agents:
  my-agent:
    command: python
    args: ["my_agent.py"]
```

### Example: Shell Script Agent

```bash
#!/bin/bash
# my_agent.sh

# Read from stdin
read -r prompt

# Process...
echo "Received: $prompt"
```

```yaml
agents:
  shell-agent:
    command: bash
    args: ["my_agent.sh"]
```

## Listing Configured Agents

View all configured agents:

```bash
relay list-agents
```

Example output:

```
┏━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Name        ┃ Command ┃ Args                ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ claude-code │ claude  │ --verbose           │
│ opencode    │ opencode│                     │
│ aider       │ aider   │ --no-git --stream   │
└─────────────┴─────────┴─────────────────────┘
```
