# API Overview

Relay provides a Python API for programmatic use. The API is organized into several modules:

## Modules

| Module | Description |
|--------|-------------|
| `relay.cli` | Command-line interface |
| `relay.models` | Pydantic models for configuration |
| `relay.executor` | Pipeline execution engine |
| `relay.config` | Configuration loading utilities |
| `relay.cache` | Caching system |
| `relay.templates` | Template management |
| `relay.dashboard` | Terminal dashboard |

## Quick Example

```python
from pathlib import Path
from relay.config import load_config, load_pipeline
from relay.executor import PipelineExecutor

# Load configurations
global_config = load_config(Path("relay.yml"))
pipeline = load_pipeline(Path("pipeline.yml"))

# Execute pipeline
executor = PipelineExecutor()
results = executor.execute(pipeline, global_config.agents)

# Check results
for result in results:
    print(f"{result.step_name}: {'✓' if result.success else '✗'}")
```

## Installation for API Use

> **Note: PyPI package coming soon. Install from source for now.**

```bash
git clone https://github.com/bruehstdio/relay.git
cd relay
pip install -e ".[dev]"
```

<!-- ```bash
pip install relay-coder
``` -->

## Type Safety

Relay uses Pydantic models for type-safe configuration:

```python
from relay.models import PipelineConfig, AgentConfig, StepConfig

# Create configuration programmatically
agent = AgentConfig(
    command="claude",
    args=["--verbose"],
    timeout=300
)

step = StepConfig(
    name="analyze",
    agent="claude-code",
    prompt="Analyze the code",
    output="analysis.md"
)

pipeline = PipelineConfig(
    name="my-pipeline",
    steps=[step]
)
```

## Error Handling

All API functions raise typed exceptions:

```python
from relay.templates import TemplateNotFoundError, TemplateVersionError

try:
    template = manager.load_template("unknown@1.0.0")
except TemplateNotFoundError:
    print("Template not found")
except TemplateVersionError:
    print("Invalid version format")
```
