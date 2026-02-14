# Parallel Processing Example

Examples of parallel execution patterns for various use cases.

## Pattern 1: Multi-Agent Analysis

Run different AI models/agents on the same task and compare results:

```yaml
name: "multi-agent-analysis"
description: "Run multiple agents on the same problem"

steps:
  - name: problem-analysis
    parallel:
      - name: claude-analysis
        agent: claude-code
        prompt: |
          Analyze this architectural problem and propose a solution:
          
          We need to handle 10,000 requests per second with
          sub-100ms latency. Current system struggles at 1,000 rps.
          
          Consider:
          - Caching strategies
          - Database optimization
          - Load balancing
          - Horizontal scaling
        output: claude-solution.md
      
      - name: opencode-analysis
        agent: opencode
        prompt: |
          Analyze this architectural problem and propose a solution:
          
          We need to handle 10,000 requests per second with
          sub-100ms latency. Current system struggles at 1,000 rps.
          
          Focus on:
          - Specific technologies (Redis, Kafka, etc.)
          - Implementation details
          - Cost considerations
        output: opencode-solution.md
      
      - name: aider-analysis
        agent: aider
        prompt: |
          Analyze this architectural problem and propose a solution:
          
          We need to handle 10,000 requests per second with
          sub-100ms latency. Current system struggles at 1,000 rps.
          
          Provide:
          - Code examples
          - Configuration snippets
          - Deployment architecture
        output: aider-solution.md
    
    parallel_strategy: concat
    output: all-solutions.md

  - name: synthesize
    agent: claude-code
    prompt: |
      Review all three proposed solutions from all-solutions.md.
      
      Create a synthesis that:
      1. Identifies common themes
      2. Highlights unique insights from each approach
      3. Proposes a hybrid solution combining the best elements
      4. Lists implementation phases
    input: all-solutions.md
    output: final-recommendation.md
```

## Pattern 2: File Batch Processing

Process multiple files in parallel:

```yaml
name: "batch-file-processing"
description: "Process multiple files simultaneously"

steps:
  - name: discover-files
    agent: opencode
    prompt: |
      Find all Python files in the src/ directory and list them.
      Format as one file per line.
    output: files.txt

  - name: process-files
    parallel:
      - name: process-models
        agent: claude-code
        prompt: |
          Review all model files (files containing "class.*Model" or in models/)
          and generate documentation for the data models.
        output: models-docs.md
      
      - name: process-views
        agent: opencode
        prompt: |
          Review all view/controller files and document the API endpoints.
        output: views-docs.md
      
      - name: process-utils
        agent: claude-code
        prompt: |
          Review utility/helper files and document the common functions.
        output: utils-docs.md
      
      - name: process-tests
        agent: opencode
        prompt: |
          Review test files and summarize test coverage and patterns.
        output: tests-docs.md
    
    parallel_strategy: concat
    output: all-docs.md

  - name: generate-index
    agent: claude-code
    prompt: |
      Create a documentation index that combines and organizes
      all the generated documentation from all-docs.md.
      
      Include:
      - Table of contents
      - Cross-references between sections
      - Getting started guide
    input: all-docs.md
    output: README.md
```

## Pattern 3: Map-Reduce

Map a task across multiple items, then reduce the results:

```yaml
name: "map-reduce-analysis"
description: "Analyze multiple components and aggregate results"

steps:
  - name: map-analysis
    description: "Analyze each component independently"
    parallel:
      - name: analyze-auth
        agent: claude-code
        prompt: |
          Analyze the authentication module for:
          - Security vulnerabilities
          - Performance bottlenecks
          - Code quality issues
        output: auth-analysis.md
      
      - name: analyze-database
        agent: opencode
        prompt: |
          Analyze the database layer for:
          - Query optimization opportunities
          - Index recommendations
          - Connection pool tuning
        output: database-analysis.md
      
      - name: analyze-api
        agent: claude-code
        prompt: |
          Analyze the API layer for:
          - REST best practices
          - Error handling
          - Rate limiting
        output: api-analysis.md
      
      - name: analyze-frontend
        agent: opencode
        prompt: |
          Analyze the frontend for:
          - Accessibility issues
          - Performance optimization
          - State management
        output: frontend-analysis.md
    
    parallel_strategy: json
    output: component-analyses.json

  - name: reduce-priorities
    agent: claude-code
    prompt: |
      Read the component analyses from component-analyses.json.
      
      Create a prioritized action plan:
      1. List all issues found across components
      2. Assign severity (Critical, High, Medium, Low)
      3. Estimate effort for each fix
      4. Create a phased implementation plan
      5. Identify any cross-component dependencies
    input: component-analyses.json
    output: action-plan.md
```

## Pattern 4: First Success

Try multiple approaches, use the first successful one:

```yaml
name: "first-success-pattern"
description: "Try multiple solutions, use first that works"

steps:
  - name: attempt-fix
    description: "Try different agents to fix the issue"
    parallel:
      - name: claude-fix
        agent: claude-code
        prompt: |
          Fix this bug: Users report intermittent 500 errors
          on the /api/orders endpoint during peak hours.
          
          Look for:
          - Race conditions
          - Resource exhaustion
          - Unhandled exceptions
        output: claude-fix.patch
      
      - name: opencode-fix
        agent: opencode
        prompt: |
          Fix this bug: Users report intermittent 500 errors
          on the /api/orders endpoint during peak hours.
          
          Consider:
          - Database connection issues
          - Memory leaks
          - Third-party service failures
        output: opencode-fix.patch
      
      - name: aider-fix
        agent: aider
        prompt: |
          Fix this bug: Users report intermittent 500 errors
          on the /api/orders endpoint during peak hours.
          
          Apply the fix directly to the codebase.
        output: aider-fix.patch
    
    parallel_strategy: first
    output: fix.patch

  - name: validate-fix
    agent: claude-code
    prompt: |
      Review the proposed fix from fix.patch:
      - Does it address the root cause?
      - Are there any side effects?
      - Is the solution maintainable?
      
      Provide a go/no-go recommendation.
    input: fix.patch
    output: fix-validation.md
```

## Pattern 5: Staged Parallelism

Different stages with parallel execution within each:

```yaml
name: "staged-parallel-pipeline"
description: "Multiple stages with internal parallelism"

steps:
  # Stage 1: Parallel discovery
  - name: discovery
    parallel:
      - name: discover-routes
        agent: opencode
        prompt: "List all API routes in the application"
        output: routes.txt
      
      - name: discover-models
        agent: claude-code
        prompt: "List all data models in the application"
        output: models.txt
      
      - name: discover-dependencies
        agent: opencode
        prompt: "List all external dependencies"
        output: dependencies.txt
    
    parallel_strategy: concat
    output: discovery-results.md

  # Stage 2: Parallel analysis (depends on discovery)
  - name: analysis
    needs:
      - discovery
    parallel:
      - name: security-analysis
        agent: claude-code
        prompt: |
          Review discovery-results.md and identify security concerns
          for routes, models, and dependencies.
        input: discovery-results.md
        output: security-analysis.md
      
      - name: performance-analysis
        agent: opencode
        prompt: |
          Review discovery-results.md and identify performance
          optimization opportunities.
        input: discovery-results.md
        output: performance-analysis.md
    
    parallel_strategy: concat
    output: analysis-results.md

  # Stage 3: Single synthesis step
  - name: recommendations
    needs:
      - analysis
    agent: claude-code
    prompt: |
      Review analysis-results.md and create prioritized
      recommendations for the team.
    input: analysis-results.md
    output: recommendations.md
```

## Parallel Strategy Comparison

| Strategy | Use Case | Output Format |
|----------|----------|---------------|
| `concat` | Combine multiple analyses | Plain text concatenation |
| `json` | Structured data processing | JSON object |
| `first` | Redundant attempts | Single successful output |

## Performance Tips

1. **Match agent to task** — Use faster agents for simple tasks
2. **Limit parallelism** — Too many parallel steps can overwhelm
3. **Use appropriate strategy** — Choose based on how you'll use the output
4. **Consider dependencies** — Only parallelize independent tasks
