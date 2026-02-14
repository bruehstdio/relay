# Pipelines

Pipelines define the sequence of steps that Relay executes. Each step runs an AI agent and can pass artifacts to subsequent steps.

## Basic Pipeline

```yaml
name: "simple-pipeline"
description: "A basic three-step pipeline"

steps:
  - name: analyze
    agent: claude-code
    prompt: "Analyze the codebase structure"
    output: analysis.md

  - name: plan
    agent: opencode
    prompt: "Create a plan based on the analysis"
    input: analysis.md
    output: plan.md

  - name: implement
    agent: aider
    prompt: "Implement the plan"
    input: plan.md
```

## Artifact Passing

Steps automatically receive output from previous steps:

```yaml
steps:
  - name: step1
    agent: claude-code
    prompt: "Create a design document"
    output: design.md
    # Output saved to .relay/artifacts/design.md

  - name: step2
    agent: opencode
    prompt: "Implement based on the design"
    input: design.md
    # Explicitly reads design.md

  - name: step3
    agent: aider
    prompt: "Review the implementation"
    # Automatically receives step2's output if no input specified
```

## Parallel Execution

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
    
    parallel_strategy: concat
    output: review-results.txt
```

### Parallel Strategies

| Strategy | Description |
|----------|-------------|
| `concat` | Concatenate all outputs (default) |
| `json` | Merge as JSON object |
| `first` | Use first successful output |

## Conditional Steps

Execute steps based on conditions:

```yaml
steps:
  - name: test
    agent: opencode
    prompt: "Run all tests"
    if: "env.RUN_TESTS != 'false'"

  - name: deploy
    agent: claude-code
    prompt: "Deploy to production"
    if: "steps.test.success"

  - name: notify-failure
    agent: claude-code
    prompt: "Notify team of failure"
    if: "steps.test.failed"
```

### Condition Types

| Condition | Description |
|-----------|-------------|
| `env.VAR == 'value'` | Environment variable comparison |
| `env.VAR` | Environment variable exists and is not empty |
| `file.exists('path')` | File exists |
| `steps.step_name.success` | Previous step succeeded |
| `steps.step_name.failed` | Previous step failed |
| `steps.step_name.exit_code == N` | Exit code comparison |
| `always` | Always run |
| `never` | Never run |

## Retry Configuration

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

### Retry Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_attempts` | int | `1` | Maximum number of attempts |
| `backoff` | string | `exponential` | Backoff strategy: `linear` or `exponential` |
| `delay` | string/int | `5s` | Initial delay between retries |
| `max_delay` | string/int | `60s` | Maximum delay between retries |

## Working Directory

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

## Error Handling

Control pipeline behavior on errors:

```yaml
steps:
  - name: optional-check
    agent: opencode
    prompt: "Run optional check"
    continue_on_error: true
    # Pipeline continues even if this step fails

  - name: critical-step
    agent: claude-code
    prompt: "Critical operation"
    on_error: fail
    # Pipeline stops on failure (default)
```

## Step Dependencies

Define explicit dependencies between steps:

```yaml
steps:
  - name: build
    agent: opencode
    prompt: "Build the project"

  - name: test
    agent: claude-code
    prompt: "Run tests"
    needs:
      - build
    # Waits for build to complete

  - name: deploy
    agent: claude-code
    prompt: "Deploy"
    needs:
      - test
    # Waits for test to complete
```

## Timeout Configuration

Set per-step timeouts:

```yaml
steps:
  - name: quick-step
    agent: opencode
    prompt: "Quick task"
    timeout: 30s

  - name: long-step
    agent: claude-code
    prompt: "Long running task"
    timeout: 10m

  - name: custom-step
    agent: aider
    prompt: "Custom timeout"
    timeout: 3600  # seconds
```

Duration formats:

- `30s` — 30 seconds
- `5m` — 5 minutes
- `1h` — 1 hour
- `3600` — 3600 seconds (numeric)
