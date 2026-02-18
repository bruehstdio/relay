# Basic Pipeline Example

A simple, minimal pipeline to get you started with Relay.

## Overview

This example demonstrates a basic three-step pipeline:
1. **Analyze** — Analyze the codebase
2. **Plan** — Create an implementation plan
3. **Implement** — Write the code

## Pipeline

```yaml
name: "basic-pipeline"
description: "A simple three-step pipeline for feature implementation"

steps:
  - name: analyze
    agent: claude-code
    prompt: |
      Analyze the current codebase structure.
      Identify:
      - Main components and their relationships
      - Existing patterns and conventions
      - Where new features should be added
      
      Write a brief summary to analysis.md.
    output: analysis.md

  - name: plan
    agent: opencode
    prompt: |
      Based on the analysis in analysis.md, create a detailed
      implementation plan for adding user authentication.
      
      Include:
      - Files to create/modify
      - Key functions/classes needed
      - Dependencies to add
      
      Write the plan to plan.md.
    input: analysis.md
    output: plan.md

  - name: implement
    agent: aider
    prompt: |
      Implement the authentication feature according to plan.md.
      
      Requirements:
      - Login/logout functionality
      - Password hashing
      - Session management
      - Basic error handling
      
      Make the changes directly to the codebase.
    input: plan.md
    output: implementation-summary.md
```

## How It Works

1. **Analysis Step** — Uses Claude Code to understand the codebase structure
2. **Planning Step** — Uses OpenCode to create a detailed implementation plan
3. **Implementation Step** — Uses Aider to make the actual code changes

## Running the Pipeline

```bash
# Save the pipeline to a file
cat > basic-pipeline.yml << 'EOF'
[name: "basic-pipeline"...]
EOF

# Run the pipeline
relay run --config basic-pipeline.yml
```

## Expected Output

```
╭────────── Pipeline: basic-pipeline ──────────╮
│ A simple three-step pipeline for feature     │
│ implementation                               │
╰──────────────────────────────────────────────╯

✓ Step 1: analyze (4523ms)
✓ Step 2: plan (3241ms)
✓ Step 3: implement (8934ms)

Pipeline complete: 3/3 steps succeeded
Total time: 16698ms
```

## Artifacts

After running, you'll find these files in `.relay/artifacts/`:

| File | Description |
|------|-------------|
| `analysis.md` | Codebase analysis summary |
| `plan.md` | Implementation plan |
| `implementation-summary.md` | Summary of changes made |

## Variations

### Single-Agent Version

Use just one agent for all steps:

```yaml
name: "single-agent-pipeline"
steps:
  - name: analyze
    agent: claude-code
    prompt: "Analyze the codebase"
    output: analysis.md

  - name: plan
    agent: claude-code
    prompt: "Create a plan based on analysis.md"
    input: analysis.md
    output: plan.md

  - name: implement
    agent: claude-code
    prompt: "Implement according to plan.md"
    input: plan.md
```

### Two-Step Version

Combine analysis and planning:

```yaml
name: "minimal-pipeline"
steps:
  - name: analyze-and-plan
    agent: claude-code
    prompt: |
      Analyze the codebase and create an implementation plan
      for adding user authentication. Write to plan.md.
    output: plan.md

  - name: implement
    agent: aider
    prompt: |
      Implement the authentication feature according to plan.md.
    input: plan.md
```

## Next Steps

- Add [parallel execution](parallel.md) for faster processing
- Add [conditional steps](deployment.md) for different environments
- Use [templates](../templates.md) to reuse this pattern
