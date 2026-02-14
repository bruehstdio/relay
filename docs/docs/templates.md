# Templates

Templates allow you to define reusable pipeline patterns and share them across projects.

## Overview

Templates provide:

- Reusable pipeline structures
- Version-controlled configurations
- Easy project initialization
- Team standardization

## Using Templates

### List Available Templates

```bash
relay template list
```

### Show Template Details

```bash
relay template show python-project
relay template show python-project@1.0.0
```

### Initialize with Template

```bash
relay init my-project --template python-project
```

## Template Locations

Templates are loaded from two locations:

1. **Built-in templates** — Packaged with Relay
2. **User templates** — `~/.relay/templates/`

User templates override built-in templates with the same name.

## Installing Built-in Templates

Copy built-in templates to your user directory:

```bash
relay template install
```

This makes them available for customization.

## Template Format

Templates are YAML files with the same structure as pipeline files:

```yaml
# python-project.yml
name: "python-project"
description: "Template for Python projects with linting and testing"

steps:
  - name: analyze
    agent: claude-code
    prompt: |
      Analyze the Python codebase and identify:
      - Code quality issues
      - Missing type hints
      - Documentation gaps
    output: analysis.md

  - name: fix
    agent: opencode
    prompt: |
      Based on analysis.md, fix the identified issues.
    input: analysis.md

  - name: test
    agent: claude-code
    prompt: |
      Run tests and fix any failures.
```

## Template Inheritance

Extend templates with custom configuration:

```yaml
# pipeline.yml
name: "my-python-project"
description: "My custom Python project pipeline"
template: python-project@1.0.0

# Override specific steps
steps:
  - name: analyze
    agent: opencode  # Use opencode instead of claude-code
  
  - name: custom-step
    agent: aider
    prompt: "Additional custom analysis"
    after: test  # Add after test step
```

### Override Rules

1. **Name and description** — User values override template
2. **Steps** — User steps override template steps by name
3. **New steps** — Added to the end (or specify position)

## Creating Custom Templates

### 1. Create Template File

Create a YAML file in `~/.relay/templates/`:

```bash
mkdir -p ~/.relay/templates
cat > ~/.relay/templates/my-template.yml << 'EOF'
name: "my-template"
description: "My custom pipeline template"

steps:
  - name: step1
    agent: claude-code
    prompt: "First step"
    output: result1.txt

  - name: step2
    agent: opencode
    prompt: "Second step"
    input: result1.txt
    output: result2.txt
EOF
```

### 2. Version Your Template

Use versioning for template changes:

```bash
# Create versioned template
cp my-template.yml my-template@1.0.0.yml

# Update with breaking changes
cp my-template.yml my-template@2.0.0.yml
```

### 3. Reference with Version

```yaml
template: my-template@1.0.0
```

## Template Reference Format

Templates can be referenced as:

| Format | Description |
|--------|-------------|
| `template-name` | Latest version |
| `template-name@1.0.0` | Specific version |

## Example Templates

### Python Project

```yaml
name: "python-project"
description: "Python project with testing and linting"

steps:
  - name: lint
    agent: opencode
    prompt: "Run ruff and fix linting issues"
    output: lint-report.txt

  - name: type-check
    agent: claude-code
    prompt: "Run mypy and fix type errors"
    output: type-report.txt

  - name: test
    agent: opencode
    prompt: "Run pytest and fix failing tests"
    output: test-report.txt
```

### Web Development

```yaml
name: "web-project"
description: "Web development with frontend and backend"

steps:
  - name: frontend-review
    parallel:
      - name: html-check
        agent: claude-code
        prompt: "Review HTML structure"
        output: html-review.txt
      
      - name: css-check
        agent: claude-code
        prompt: "Review CSS/ styling"
        output: css-review.txt
      
      - name: js-check
        agent: opencode
        prompt: "Review JavaScript code"
        output: js-review.txt
    
    parallel_strategy: concat
    output: frontend-review.txt

  - name: backend-review
    agent: claude-code
    prompt: "Review backend code"
    output: backend-review.txt

  - name: integration
    agent: opencode
    prompt: "Review integration points"
    input: frontend-review.txt
    output: final-report.txt
```

### Documentation

```yaml
name: "docs-project"
description: "Documentation improvement pipeline"

steps:
  - name: analyze
    agent: claude-code
    prompt: |
      Analyze the documentation for:
      - Missing sections
      - Outdated information
      - Clarity issues
    output: analysis.md

  - name: improve
    agent: opencode
    prompt: |
      Based on analysis.md, improve the documentation.
    input: analysis.md
    output: improved-docs/
```

## Best Practices

1. **Version your templates** — Use semantic versioning
2. **Document your templates** — Include clear descriptions
3. **Keep templates focused** — One template per use case
4. **Test templates** — Run them before sharing
5. **Share with team** — Commit user templates to version control
