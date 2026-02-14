# Models API

The `relay.models` module provides Pydantic models for configuration and execution.

## Module Reference

::: relay.models
    options:
      show_source: true
      show_root_heading: true

## Core Models

### AgentConfig

Configuration for an AI agent.

```python
from relay.models import AgentConfig

agent = AgentConfig(
    command="claude",
    args=["--verbose"],
    env={"CLAUDE_CODE_DEBUG": "1"},
    timeout=300
)
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `command` | `str` | Required | Command to run |
| `args` | `list[str]` | `[]` | Default arguments |
| `env` | `dict[str, str]` | `{}` | Environment variables |
| `timeout` | `int` | `300` | Timeout in seconds |

### StepConfig

Configuration for a pipeline step.

```python
from relay.models import StepConfig, RetryConfig

step = StepConfig(
    name="analyze",
    agent="claude-code",
    prompt="Analyze the code",
    input="previous.txt",
    output="result.txt",
    working_dir="./subdir",
    continue_on_error=False,
    timeout=600,
    retry=RetryConfig(max_attempts=3),
    needs=["previous-step"],
    if_="env.RUN_ANALYSIS == 'true'"
)
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | Required | Step name |
| `agent` | `str \| None` | `None` | Agent to use |
| `prompt` | `str \| None` | `None` | Instructions |
| `input` | `str \| None` | `None` | Input file |
| `output` | `str \| None` | `None` | Output file |
| `working_dir` | `Path \| None` | `None` | Working directory |
| `continue_on_error` | `bool` | `False` | Continue on error |
| `on_error` | `ErrorMode` | `FAIL` | Error handling |
| `timeout` | `str \| int \| None` | `None` | Timeout |
| `retry` | `RetryConfig \| None` | `None` | Retry config |
| `parallel` | `list[ParallelStepConfig] \| None` | `None` | Parallel steps |
| `parallel_strategy` | `str` | `concat` | Merge strategy |
| `needs` | `list[str]` | `[]` | Dependencies |
| `if_` | `str \| None` | `None` | Condition |
| `cache` | `StepCacheConfig \| None` | `None` | Cache config |

### PipelineConfig

Configuration for a pipeline.

```python
from relay.models import PipelineConfig

pipeline = PipelineConfig(
    name="my-pipeline",
    description="A test pipeline",
    template="python-project",
    steps=[step1, step2],
    cache=cache_config
)
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | Required | Pipeline name |
| `description` | `str \| None` | `None` | Description |
| `template` | `str \| None` | `None` | Template reference |
| `steps` | `list[StepConfig]` | Required | Steps |
| `cache` | `CacheConfig \| None` | `None` | Cache config |

### RelayConfig

Root configuration.

```python
from relay.models import RelayConfig

config = RelayConfig(
    agents={"claude-code": agent_config},
    pipelines={"default": ["step1", "step2"]},
    cache=cache_config
)
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `agents` | `dict[str, AgentConfig]` | Defaults | Agent configs |
| `pipelines` | `dict[str, list[str]]` | `{}` | Named pipelines |
| `cache` | `CacheConfig` | Local | Cache config |

### StepResult

Result of executing a step.

```python
from relay.models import StepResult

result = StepResult(
    step_name="analyze",
    success=True,
    output="Analysis complete",
    error=None,
    duration_ms=1234,
    artifacts=[Path("result.txt")],
    attempts=1
)
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `step_name` | `str` | Required | Step name |
| `success` | `bool` | Required | Success status |
| `output` | `str` | `""` | Output content |
| `error` | `str \| None` | `None` | Error message |
| `duration_ms` | `int` | `0` | Duration in ms |
| `artifacts` | `list[Path]` | `[]` | Output files |
| `attempts` | `int` | `1` | Number of attempts |
| `timed_out` | `bool` | `False` | Timed out |

## Supporting Models

### RetryConfig

```python
from relay.models import RetryConfig, BackoffStrategy

retry = RetryConfig(
    max_attempts=3,
    backoff=BackoffStrategy.EXPONENTIAL,
    delay="5s",
    max_delay="60s"
)
```

### CacheConfig

```python
from relay.models import CacheConfig

cache = CacheConfig(
    backend="local",
    local_path=Path("~/.relay/cache")
)
```

### StepCacheConfig

```python
from relay.models import StepCacheConfig, CacheAction

step_cache = StepCacheConfig(
    paths=["node_modules", "package-lock.json"],
    key="npm-{{ hash('package-lock.json') }}",
    action=CacheAction.RESTORE_AND_SAVE
)
```

## Enums

### BackoffStrategy

- `LINEAR` — Linear backoff
- `EXPONENTIAL` — Exponential backoff

### ErrorMode

- `FAIL` — Stop pipeline on error
- `CONTINUE` — Continue pipeline on error

### CacheAction

- `RESTORE` — Only restore from cache
- `SAVE` — Only save to cache
- `RESTORE_AND_SAVE` — Both
