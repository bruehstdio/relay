# Multi-Agent Pipeline Example

Demonstrates chaining multiple AI agents together, each contributing their unique strengths.

## Overview

This example shows how different agents can work together on the same task:
- **Claude Code** — Planning and architecture
- **OpenCode** — Fast implementation
- **Aider** — Multi-file editing
- **Codex** — Review and testing

## Pipeline

```yaml
name: "multi-agent-feature"
description: "Multiple agents collaborating on feature implementation"

steps:
  # Step 1: Architecture (Claude Code)
  - name: architecture
    agent: claude-code
    prompt: |
      Design a REST API for a task management system.
      
      Requirements:
      - User authentication via JWT
      - CRUD operations for tasks
      - Task priorities and deadlines
      - Filtering and sorting
      
      Deliverables:
      - API endpoint specification
      - Data models
      - Authentication flow
      
      Write to architecture.md.
    output: architecture.md

  # Step 2: Database Schema (OpenCode)
  - name: database
    agent: opencode
    prompt: |
      Based on architecture.md, design the database schema.
      
      Include:
      - Table definitions (PostgreSQL)
      - Indexes for performance
      - Foreign key relationships
      - Migration script
      
      Write to schema.sql.
    input: architecture.md
    output: schema.sql

  # Step 3: Backend Implementation (Aider)
  - name: backend
    agent: aider
    prompt: |
      Implement the backend API according to architecture.md.
      Use the schema from schema.sql.
      
      Tech stack:
      - Python with FastAPI
      - SQLAlchemy for ORM
      - Pydantic for validation
      
      Create:
      - models.py (SQLAlchemy models)
      - schemas.py (Pydantic models)
      - auth.py (JWT authentication)
      - routes.py (API endpoints)
      - main.py (application entry point)
    input: |
      architecture.md
      schema.sql
    output: backend-summary.md

  # Step 4: Frontend Implementation (OpenCode)
  - name: frontend
    agent: opencode
    prompt: |
      Create a React frontend for the task management API.
      
      Features needed:
      - Login/logout
      - Task list with filtering
      - Create/edit task forms
      - Responsive design
      
      Write to frontend.jsx.
    input: architecture.md
    output: frontend.jsx

  # Step 5: Testing (Codex)
  - name: tests
    agent: codex
    prompt: |
      Write comprehensive tests for the backend API.
      
      Include:
      - Unit tests for models
      - Integration tests for API endpoints
      - Authentication tests
      - Edge cases and error handling
      
      Use pytest. Write to test_api.py.
    input: |
      architecture.md
      schema.sql
      backend-summary.md
    output: test_api.py

  # Step 6: Review (Claude Code)
  - name: review
    agent: claude-code
    prompt: |
      Review the complete implementation:
      - architecture.md (requirements)
      - schema.sql (database)
      - backend-summary.md (API implementation)
      - frontend.jsx (UI)
      - test_api.py (tests)
      
      Provide:
      1. Code quality assessment
      2. Security review
      3. Performance considerations
      4. Recommendations for improvement
      
      Write to review-report.md.
    input: |
      architecture.md
      schema.sql
      backend-summary.md
      frontend.jsx
      test_api.py
    output: review-report.md

  # Step 7: Documentation (OpenCode)
  - name: documentation
    agent: opencode
    prompt: |
      Create comprehensive documentation:
      
      1. README.md — Project overview and setup
      2. API.md — API documentation with examples
      3. DEPLOYMENT.md — Deployment guide
      
      Use architecture.md and backend-summary.md as sources.
    input: |
      architecture.md
      backend-summary.md
    output: docs-summary.md
```

## How It Works

Each step leverages a different agent's strengths:

| Step | Agent | Strength Used |
|------|-------|---------------|
| Architecture | Claude Code | Complex reasoning, design |
| Database | OpenCode | Fast, precise technical work |
| Backend | Aider | Multi-file code editing |
| Frontend | OpenCode | Diverse capabilities |
| Tests | Codex | OpenAI model expertise |
| Review | Claude Code | Critical analysis |
| Documentation | OpenCode | Efficient text generation |

## Running the Pipeline

```bash
# Run the multi-agent pipeline
relay run --config multi-agent.yml
```

## Key Benefits

1. **Specialization** — Each agent does what it does best
2. **Diversity** — Different approaches to the same problem
3. **Quality** — Multiple perspectives on the final output
4. **Efficiency** — Parallel agents where possible

## Variations

### Parallel Development

Develop backend and frontend simultaneously:

```yaml
steps:
  - name: architecture
    agent: claude-code
    prompt: "Design the system"
    output: architecture.md

  - name: implementation
    parallel:
      - name: backend
        agent: aider
        prompt: "Implement backend"
        input: architecture.md
        output: backend.md
      
      - name: frontend
        agent: opencode
        prompt: "Implement frontend"
        input: architecture.md
        output: frontend.md
    
    parallel_strategy: concat
    output: implementation.md

  - name: integration
    agent: claude-code
    prompt: "Review and integrate"
    input: implementation.md
```

### Agent Fallback

Try multiple agents for the same task:

```yaml
steps:
  - name: code-generation
    parallel:
      - name: try-claude
        agent: claude-code
        prompt: "Generate the code"
        output: claude-version.py
      
      - name: try-opencode
        agent: opencode
        prompt: "Generate the code"
        output: opencode-version.py
    
    parallel_strategy: first
    output: generated-code.py
```

## Tips for Multi-Agent Pipelines

1. **Clear Handoffs** — Make sure outputs are well-formatted for the next agent
2. **Specific Prompts** — Each agent needs clear instructions
3. **Error Handling** — Use `continue_on_error` for non-critical steps
4. **Input Management** — Use the `input` field to pass context explicitly
