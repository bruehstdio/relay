# Examples Overview

This section contains practical examples of using Relay for various workflows.

## Available Examples

### [Basic Pipeline](basic-pipeline.md)

A simple three-step pipeline perfect for getting started:

- Codebase analysis
- Implementation planning
- Code generation

### [Multi-Agent Pipeline](multi-agent.md)

Demonstrates chaining multiple AI agents together:

- Architecture design (Claude Code)
- Database schema (OpenCode)
- Backend implementation (Aider)
- Frontend development (OpenCode)
- Testing (Codex)
- Review (Claude Code)

### [GitHub Integration](github-integration.md)

Automate GitHub workflows:

- Issue analysis to PR creation
- Automated code review
- Release note generation

### [Code Review Pipeline](code-review.md)

A comprehensive code review pipeline that runs multiple checks in parallel:

- Security analysis
- Performance review
- Style checking
- Summary generation

### [Deployment Pipeline](deployment.md)

A deployment workflow with conditional steps:

- Testing
- Building
- Deploying to staging/production
- Notifications

### [Parallel Processing](parallel.md)

Examples of parallel execution patterns:

- Multi-agent analysis
- File processing
- Map-reduce patterns

## Quick Examples

### Simple Two-Step Pipeline

```yaml
name: "simple"
steps:
  - name: analyze
    agent: claude-code
    prompt: "Analyze the code"
    output: analysis.md

  - name: fix
    agent: opencode
    prompt: "Fix the issues"
    input: analysis.md
```

### Parallel Code Review

```yaml
name: "parallel-review"
steps:
  - name: review
    parallel:
      - name: security
        agent: claude-code
        prompt: "Check security"
        output: sec.txt
      - name: performance
        agent: opencode
        prompt: "Check performance"
        output: perf.txt
    parallel_strategy: concat
    output: review.txt
```

### Conditional Deployment

```yaml
name: "deploy"
steps:
  - name: test
    agent: opencode
    prompt: "Run tests"
  
  - name: deploy
    agent: claude-code
    prompt: "Deploy to prod"
    if: "steps.test.success and env.BRANCH == 'main'"
```

## Running Examples

1. Copy the example YAML to a file (e.g., `pipeline.yml`)
2. Ensure you have the required agents installed
3. Run with: `relay run --config pipeline.yml`

## Contributing Examples

Have a useful pipeline example? Consider contributing it!

1. Create your example in the examples directory
2. Add documentation explaining the use case
3. Submit a pull request
