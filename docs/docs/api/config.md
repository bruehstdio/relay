# Config API

The `relay.config` module provides configuration loading utilities.

## Module Reference

::: relay.config
    options:
      show_source: true
      show_root_heading: true

## Functions

### load_config

Load Relay global configuration from a YAML file.

```python
from relay.config import load_config
from pathlib import Path

config = load_config(Path("relay.yml"))

# Access agents
for name, agent in config.agents.items():
    print(f"{name}: {agent.command}")

# Access cache config
print(config.cache.backend)
```

**Signature:**

```python
def load_config(path: Path) -> RelayConfig
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `Path` | Path to YAML file |

**Returns:**

`RelayConfig` object.

**Example:**

```python
from relay.config import load_config

config_path = Path("relay.yml")
if config_path.exists():
    config = load_config(config_path)
else:
    # Use defaults
    from relay.models import RelayConfig
    config = RelayConfig()
```

### load_pipeline

Load a pipeline configuration from a YAML file.

```python
from relay.config import load_pipeline

pipeline = load_pipeline(Path("pipeline.yml"))

# Access pipeline info
print(pipeline.name)
print(pipeline.description)

# Access steps
for step in pipeline.steps:
    print(f"{step.name}: {step.agent}")
```

**Signature:**

```python
def load_pipeline(path: Path) -> PipelineConfig
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `Path` | Path to YAML file |

**Returns:**

`PipelineConfig` object.

**Example:**

```python
from relay.config import load_pipeline
from relay.executor import PipelineExecutor

pipeline = load_pipeline(Path("pipeline.yml"))
executor = PipelineExecutor()
results = executor.execute(pipeline, global_config.agents)
```

### find_config_file

Find a Relay configuration file in the current directory or parents.

```python
from relay.config import find_config_file

config_path = find_config_file()
if config_path:
    config = load_config(config_path)
    print(f"Found config at: {config_path}")
else:
    print("No config file found")
```

**Signature:**

```python
def find_config_file() -> Path | None
```

**Returns:**

Path to config file or `None` if not found.

**Search Order:**

1. `relay.yml`
2. `relay.yaml`
3. `.relay.yml`
4. `.relay.yaml`

Searches current directory and up to 10 parent directories.

## Environment Variable Interpolation

Both `load_config` and `load_pipeline` support environment variable interpolation:

```yaml
# relay.yml
agents:
  my-agent:
    command: ${AGENT_COMMAND:-claude}
    env:
      API_KEY: ${API_KEY}
```

**Syntax:**

| Syntax | Description |
|--------|-------------|
| `${VAR}` | Substitute environment variable |
| `${VAR:-default}` | Substitute with default value |

**Example:**

```python
import os

# Set environment variable
os.environ["MY_VAR"] = "hello"

# In config file: ${MY_VAR} -> "hello"
# In config file: ${OTHER:-default} -> "default"
```

## Complete Example

```python
from pathlib import Path
from relay.config import load_config, load_pipeline, find_config_file
from relay.executor import PipelineExecutor

def run_pipeline(pipeline_path: Path | None = None) -> None:
    # Find or load global config
    config_path = find_config_file()
    if config_path:
        global_config = load_config(config_path)
    else:
        from relay.models import RelayConfig
        global_config = RelayConfig()
    
    # Load pipeline
    if pipeline_path:
        pipeline = load_pipeline(pipeline_path)
    else:
        # Look for default pipeline files
        for name in ["pipeline.yml", "pipeline.yaml"]:
            path = Path(name)
            if path.exists():
                pipeline = load_pipeline(path)
                break
        else:
            raise FileNotFoundError("No pipeline file found")
    
    # Execute
    executor = PipelineExecutor()
    results = executor.execute(pipeline, global_config.agents)
    
    # Report
    successful = sum(1 for r in results if r.success)
    print(f"Completed: {successful}/{len(results)} steps")

if __name__ == "__main__":
    run_pipeline()
```
