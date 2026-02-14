# Configuration

Relay uses YAML-based configuration with two main files:

- **`relay.yml`** — Global configuration (agents, defaults)
- **`pipeline.yml`** — Pipeline-specific configuration (steps)

## Global Configuration (`relay.yml`)

The global configuration file defines your agents and global settings.

### File Location

Relay searches for `relay.yml` in the following order:

1. Current directory
2. Parent directories (up to 10 levels)
3. Home directory (`~/.relay.yml`)

### Example `relay.yml`

```yaml
# Define your agents
agents:
  claude-code:
    command: claude
    args: ["--verbose"]
    env:
      CLAUDE_CODE_DEBUG: "1"
    timeout: 600
  
  opencode:
    command: opencode
    env:
      OPENCODE_MODEL: claude-3-5-sonnet
    timeout: 300
  
  aider:
    command: aider
    args: ["--no-git", "--stream"]
    timeout: 900

# Named pipeline sequences
pipelines:
  default:
    - analyze
    - plan
    - implement
    - review
  
  quick:
    - analyze
    - fix

# Global cache settings
cache:
  backend: local
  local_path: ~/.relay/cache
```

### Agent Configuration

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `command` | string | Yes | — | Command to run the agent |
| `args` | list | No | `[]` | Default arguments |
| `env` | dict | No | `{}` | Environment variables |
| `timeout` | int | No | `300` | Timeout in seconds |

### Cache Configuration

```yaml
cache:
  backend: local           # or 's3'
  local_path: ~/.relay/cache
  
  # For S3 backend
  s3_bucket: my-bucket
  s3_endpoint: https://minio.example.com
  s3_region: us-east-1
  s3_access_key: ${AWS_ACCESS_KEY_ID}
  s3_secret_key: ${AWS_SECRET_ACCESS_KEY}
  s3_prefix: relay-cache/
```

## Pipeline Configuration (`pipeline.yml`)

Pipeline files define the steps to execute.

### Example `pipeline.yml`

```yaml
name: "my-pipeline"
description: "Description of what this pipeline does"

steps:
  - name: step-1
    agent: claude-code
    prompt: "Instructions for the agent"
    output: result.txt
```

### Pipeline Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Pipeline name |
| `description` | string | No | Pipeline description |
| `template` | string | No | Template reference (e.g., `python-project@1.0.0`) |
| `steps` | list | Yes | List of step definitions |

### Step Configuration

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | — | Unique step name |
| `agent` | string | Yes* | — | Agent to use (*unless using `parallel`) |
| `prompt` | string | No | — | Instructions for the agent |
| `input` | string | No | — | Input file from previous step |
| `output` | string | No | — | Output file to save |
| `working_dir` | string | No | — | Working directory for this step |
| `continue_on_error` | bool | No | `false` | Continue pipeline on error |
| `on_error` | string | No | `fail` | Error mode: `fail` or `continue` |
| `timeout` | string/int | No | — | Step timeout (e.g., `10m`, `60s`) |
| `if` | string | No | — | Condition to evaluate before running |
| `needs` | list | No | `[]` | Step dependencies |
| `retry` | object | No | — | Retry configuration |
| `cache` | object | No | — | Cache configuration for this step |
| `parallel` | list | No | — | Parallel sub-steps |
| `parallel_strategy` | string | No | `concat` | How to merge outputs: `concat`, `json`, `first` |

## Environment Variable Interpolation

Both config files support environment variable interpolation:

```yaml
name: "Pipeline for ${PROJECT_NAME}"

agents:
  deploy-agent:
    command: claude
    env:
      API_KEY: ${API_KEY}
      ENVIRONMENT: ${ENVIRONMENT:-development}

steps:
  - name: deploy
    agent: ${DEPLOY_AGENT:-claude-code}
    prompt: "Deploy to ${ENVIRONMENT}"
```

Syntax:

- `${VAR}` — Simple substitution
- `${VAR:-default}` — Substitution with default value

## Default Agents

Relay comes with pre-configured defaults for common agents:

| Agent | Command | Notes |
|-------|---------|-------|
| `claude-code` | `claude` | Anthropic's Claude Code |
| `opencode` | `opencode` | Open-source, any provider |
| `opencode-run` | `opencode run` | OpenCode run mode |
| `oh-my-opencode` | `oh-my-opencode` | OMO wrapper |
| `gemini` | `gemini` | Google's Gemini CLI |
| `aider` | `aider` | Multi-file edits |
| `codex` | `codex` | OpenAI's Codex |

These are automatically available even if not defined in your `relay.yml`. You can override any of them by defining an agent with the same name.
