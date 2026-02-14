# Code Review Example

A comprehensive code review pipeline that runs multiple analyses in parallel and produces a unified report.

## Pipeline

```yaml
name: "automated-code-review"
description: "Multi-agent code review with parallel analysis"

steps:
  - name: code-review
    description: "Run multiple code reviews in parallel"
    parallel:
      - name: security-check
        agent: claude-code
        prompt: |
          Review the codebase for security issues:
          - SQL injection vulnerabilities
          - XSS vulnerabilities
          - Insecure dependencies
          - Hardcoded secrets
          - Authentication/authorization issues
          
          Write findings to security.md with severity ratings.
        output: security.md
      
      - name: performance-check
        agent: opencode
        prompt: |
          Review the codebase for performance issues:
          - Inefficient algorithms
          - N+1 queries
          - Memory leaks
          - Unnecessary computations
          - Caching opportunities
          
          Write findings to performance.md with impact ratings.
        output: performance.md
      
      - name: style-check
        agent: claude-code
        prompt: |
          Review the codebase for:
          - Code style consistency
          - Naming conventions
          - Documentation quality
          - Type hints (if Python)
          - Code organization
          
          Write findings to style.md.
        output: style.md
      
      - name: architecture-check
        agent: opencode
        prompt: |
          Review the codebase architecture:
          - Design patterns usage
          - Separation of concerns
          - Module dependencies
          - API design
          - Test coverage
          
          Write findings to architecture.md.
        output: architecture.md
    
    parallel_strategy: concat
    output: combined-reviews.md

  - name: summarize
    agent: claude-code
    prompt: |
      Read the combined code review results from combined-reviews.md.
      Create a concise executive summary that includes:
      
      1. Overall code quality assessment
      2. Critical issues (if any) requiring immediate attention
      3. Top 3 recommendations for improvement
      4. Priority order for addressing issues
      
      Format as a professional code review report.
    input: combined-reviews.md
    output: review-summary.md

  - name: action-items
    agent: opencode
    prompt: |
      Based on review-summary.md, create actionable tickets/tasks:
      
      For each issue identified, create a task with:
      - Clear description
      - Priority (P0, P1, P2, P3)
      - Estimated effort
      - Assigned category (security/performance/style/architecture)
      
      Output as a structured markdown list.
    input: review-summary.md
    output: action-items.md
```

## How It Works

1. **Parallel Analysis** — Four different agents analyze the code simultaneously:
   - Security-focused review (Claude Code)
   - Performance review (OpenCode)
   - Style review (Claude Code)
   - Architecture review (OpenCode)

2. **Result Merging** — The `concat` strategy combines all outputs into `combined-reviews.md`

3. **Summary Generation** — Claude Code reads the combined results and creates an executive summary

4. **Action Items** — OpenCode converts findings into actionable tasks with priorities

## Usage

```bash
# Run the review
relay run --config code-review.yml

# Check results
cat .relay/artifacts/review-summary.md
cat .relay/artifacts/action-items.md
```

## Customization

### Add Custom Checks

Add more parallel sub-steps for specific concerns:

```yaml
parallel:
  # ... existing checks ...
  
  - name: accessibility-check
    agent: claude-code
    prompt: "Review for accessibility issues..."
    output: accessibility.md
```

### Change Parallel Strategy

Use JSON output for programmatic processing:

```yaml
parallel_strategy: json
# Output will be a JSON object with keys for each sub-step
```

### Use First Successful

If you just need one good result:

```yaml
parallel_strategy: first
```

## Expected Output

```
╭────── Pipeline: automated-code-review ──────╮
│ Multi-agent code review with parallel analysis│
╰───────────────────────────────────────────────╯

✓ Step 1: code-review (4 parallel tasks)
  ✓ security-check
  ✓ performance-check
  ✓ style-check
  ✓ architecture-check
✓ Step 2: summarize (2341ms)
✓ Step 3: action-items (1892ms)

Pipeline complete: 3/3 steps succeeded
Total time: 15678ms
```

## Artifacts

| File | Description |
|------|-------------|
| `security.md` | Security findings |
| `performance.md` | Performance issues |
| `style.md` | Style violations |
| `architecture.md` | Architecture concerns |
| `combined-reviews.md` | All reviews combined |
| `review-summary.md` | Executive summary |
| `action-items.md` | Actionable tasks |
