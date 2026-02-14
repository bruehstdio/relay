# Templates API

The `relay.templates` module provides template management for Relay pipelines.

## Module Reference

::: relay.templates
    options:
      show_source: true
      show_root_heading: true

## TemplateManager

Main class for managing templates.

```python
from relay.templates import TemplateManager, get_template_manager

# Get default manager
manager = get_template_manager()

# Or create custom
manager = TemplateManager(
    user_dir=Path("~/.relay/templates"),
    builtin_dir=Path("/usr/share/relay/templates"),
)
```

### Constructor

```python
TemplateManager(
    user_dir: Path | None = None,
    builtin_dir: Path | None = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_dir` | `Path \| None` | `~/.relay/templates` | User templates directory |
| `builtin_dir` | `Path \| None` | Package templates | Built-in templates directory |

### Methods

#### load_template

```python
def load_template(self, template_ref: str) -> dict[str, Any]
```

Load a template by reference.

```python
# Load latest version
data = manager.load_template("python-project")

# Load specific version
data = manager.load_template("python-project@1.0.0")
```

**Raises:**

- `TemplateNotFoundError` — Template not found
- `TemplateVersionError` — Invalid version format

#### list_templates

```python
def list_templates(self) -> list[dict[str, Any]]
```

List all available templates.

```python
templates = manager.list_templates()
for tmpl in templates:
    print(f"{tmpl['name']} @ {tmpl['version']}")
    print(f"  Source: {tmpl['source']}")
    print(f"  {tmpl['description'][:50]}...")
```

Returns list of dicts with keys:

| Key | Type | Description |
|-----|------|-------------|
| `name` | `str` | Template name |
| `version` | `str` | Template version |
| `description` | `str` | Template description |
| `source` | `str` | `'builtin'` or `'user'` |
| `file` | `str` | Path to template file |

#### show_template

```python
def show_template(self, template_ref: str) -> dict[str, Any]
```

Show detailed template information.

```python
info = manager.show_template("python-project")
print(info["name"])        # Template name
print(info["version"])     # Version
print(info["description"]) # Description
print(info["source"])      # 'builtin' or 'user'
print(info["data"])        # Template data dict
```

#### resolve_pipeline

```python
def resolve_pipeline(
    self,
    user_config: dict[str, Any],
) -> PipelineConfig
```

Resolve a pipeline with template inheritance.

```python
user_config = {
    "name": "my-project",
    "template": "python-project",
    "steps": [
        {"name": "custom-step", "agent": "opencode", "prompt": "Custom"}
    ]
}

pipeline = manager.resolve_pipeline(user_config)
```

#### install_builtin_templates

```python
def install_builtin_templates(self) -> list[str]
```

Copy built-in templates to user directory.

```python
installed = manager.install_builtin_templates()
print(f"Installed: {', '.join(installed)}")
```

## Exceptions

### TemplateNotFoundError

```python
from relay.templates import TemplateNotFoundError

try:
    template = manager.load_template("unknown")
except TemplateNotFoundError as e:
    print(f"Template not found: {e}")
```

### TemplateVersionError

```python
from relay.templates import TemplateVersionError

try:
    template = manager.load_template("template@invalid-version")
except TemplateVersionError as e:
    print(f"Invalid version: {e}")
```

## Helper Functions

### get_template_manager

```python
from relay.templates import get_template_manager

manager = get_template_manager()
```

Returns the default `TemplateManager` instance.

### _parse_template_ref

```python
from relay.templates import _parse_template_ref

name, version = _parse_template_ref("python-project@1.0.0")
print(name)     # "python-project"
print(version)  # "1.0.0"

name, version = _parse_template_ref("python-project")
print(name)     # "python-project"
print(version)  # None
```

## Template File Format

Templates are YAML files:

```yaml
# python-project@1.0.0.yml
name: "python-project"
description: "Python project template"

steps:
  - name: lint
    agent: opencode
    prompt: "Run linting"
    output: lint.txt

  - name: test
    agent: claude-code
    prompt: "Run tests"
    output: test.txt
```

## Complete Example

```python
from relay.templates import TemplateManager, TemplateNotFoundError
from relay.config import load_pipeline
from relay.executor import PipelineExecutor
import yaml

# Create manager
manager = TemplateManager()

# List templates
print("Available templates:")
for tmpl in manager.list_templates():
    print(f"  • {tmpl['name']} ({tmpl['source']})")

# Try to load a template
try:
    template_data = manager.load_template("python-project")
    print(f"\nLoaded template: {template_data['name']}")
    
    # Customize
    template_data['name'] = 'my-custom-pipeline'
    
    # Save to file
    with open('pipeline.yml', 'w') as f:
        yaml.dump(template_data, f)
    
    # Execute
    from relay.models import RelayConfig
    pipeline = manager.resolve_pipeline(template_data)
    executor = PipelineExecutor()
    results = executor.execute(pipeline, RelayConfig().agents)
    
except TemplateNotFoundError:
    print("Template not found, using default")
    # ... create default pipeline
```
