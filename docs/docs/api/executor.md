# Executor API

The `relay.executor` module provides the pipeline execution engine.

## Module Reference

::: relay.executor
    options:
      show_source: true
      show_root_heading: true

## PipelineExecutor

The main class for executing pipelines.

```python
from relay.executor import PipelineExecutor
from relay.config import load_config, load_pipeline

# Load configurations
global_config = load_config(Path("relay.yml"))
pipeline = load_pipeline(Path("pipeline.yml"))

# Create executor
executor = PipelineExecutor(working_dir=Path("./my-project"))

# Execute pipeline
results = executor.execute(pipeline, global_config.agents)

# Process results
for result in results:
    print(f"{result.step_name}: {result.success}")
```

### Constructor

```python
PipelineExecutor(working_dir: Path | None = None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `working_dir` | `Path \| None` | `cwd()` | Working directory for execution |

### Methods

#### execute

```python
def execute(
    self,
    config: PipelineConfig,
    agents: dict[str, AgentConfig]
) -> list[StepResult]
```

Execute a pipeline configuration.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `config` | `PipelineConfig` | Pipeline configuration |
| `agents` | `dict[str, AgentConfig]` | Agent configurations |

**Returns:**

List of `StepResult` objects, one per step.

**Example:**

```python
results = executor.execute(pipeline, agents)

# Check if all steps succeeded
all_success = all(r.success for r in results)

# Get total execution time
total_time = sum(r.duration_ms for r in results)
```

## Execution Flow

1. **Pipeline Start** — Display pipeline name and description
2. **Step Execution** — Execute each step in sequence
3. **Artifact Passing** — Pass output from one step to the next
4. **Error Handling** — Stop or continue based on configuration
5. **Summary** — Display execution summary

## Internal Methods

### _execute_step

Execute a single pipeline step.

```python
def _execute_step(
    self,
    step_num: int,
    step: StepConfig,
    agents: dict[str, AgentConfig],
    previous_output: Path | None,
) -> StepResult
```

### _execute_parallel_step

Execute parallel sub-steps concurrently.

```python
def _execute_parallel_step(
    self,
    step_num: int,
    step: StepConfig,
    agents: dict[str, AgentConfig],
    previous_output: Path | None,
) -> StepResult
```

### _run_agent

Run a single agent command.

```python
def _run_agent(
    self,
    agent_config: AgentConfig,
    prompt: str,
    working_dir: Path,
) -> StepResult
```

### _merge_parallel_outputs

Merge outputs from parallel steps.

```python
def _merge_parallel_outputs(
    self,
    results: list[StepResult],
    strategy: str,
) -> str
```

**Strategies:**

| Strategy | Description |
|----------|-------------|
| `concat` | Concatenate all outputs |
| `json` | Merge as JSON object |
| `first` | Use first successful output |

### _prepare_prompt

Prepare the prompt for a step.

```python
def _prepare_prompt(
    self,
    step: StepConfig,
    previous_output: Path | None,
) -> str
```

Includes:
- Step prompt
- Input file content (if specified)
- Previous step output (if no input specified)

## Artifacts

Artifacts are stored in `.relay/artifacts/`:

```python
# Access artifacts directory
artifacts_dir = executor.artifacts_dir

# List all artifacts
for artifact in results[-1].artifacts:
    print(artifact)
```

## Results

Step results contain:

```python
result = results[0]

# Basic info
print(result.step_name)      # Step name
print(result.success)        # Success status
print(result.duration_ms)    # Execution time

# Output
print(result.output)         # Stdout content
print(result.error)          # Error message (if failed)

# Artifacts
for artifact in result.artifacts:
    content = artifact.read_text()
```
