# Quick Start

This guide will walk you through creating your first Relay pipeline.

> **Note: PyPI package coming soon. For now, install from source:**
> ```bash
> git clone https://github.com/bruehstdio/relay.git
> cd relay
> pip install -e ".[dev]"
> ```

## 1. Initialize a New Project

Create a directory for your project and initialize Relay:

```bash
mkdir my-project
cd my-project
relay init
```

This creates two files:

- `relay.yml` — Global configuration with agent definitions
- `pipeline.yml` — Your pipeline definition

## 2. Configure Your Agents

Edit `relay.yml` to configure the AI agents you want to use:

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

## 3. Define Your Pipeline

Edit `pipeline.yml` to define your workflow:

```yaml
name: "my-first-pipeline"
description: "A simple three-step pipeline"

steps:
  - name: plan
    agent: claude-code
    prompt: |
      Create a plan for implementing a simple Python CLI tool
      that converts JSON to CSV. Write the plan to plan.md.
    output: plan.md

  - name: code
    agent: opencode
    prompt: |
      Based on plan.md, implement the JSON to CSV converter.
      Create a complete, working Python script.
    input: plan.md
    output: implementation.py

  - name: review
    agent: claude-code
    prompt: |
      Review implementation.py for:
      - Code quality and best practices
      - Error handling
      - Edge cases
      Suggest improvements.
    input: implementation.py
    output: review.md
```

## 4. Run the Pipeline

Execute your pipeline:

```bash
relay run
```

You'll see output like:

```
╭────────── Pipeline: my-first-pipeline ──────────╮
│ A simple three-step pipeline                    │
╰─────────────────────────────────────────────────╯

✓ Step 1: plan (4523ms)
✓ Step 2: code (8934ms)
✓ Step 3: review (3211ms)

Pipeline complete: 3/3 steps succeeded
Total time: 16668ms
```

## 5. Check the Results

Relay stores artifacts in `.relay/artifacts/`:

```bash
ls -la .relay/artifacts/
# plan.md
# implementation.py
# review.md
```

## 6. Try a Dry Run

Before running, you can preview what would execute:

```bash
relay run --dry-run
```

## Next Steps

- Learn about [Configuration](configuration.md) options
- Explore [Pipeline](pipelines.md) features
- Check out [Examples](examples/index.md)
