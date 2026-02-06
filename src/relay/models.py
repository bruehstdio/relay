"""Pydantic models for Relay configuration and execution."""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from typing import Any  # noqa: F401

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BackoffStrategy(str, Enum):
    """Backoff strategy for retries."""

    LINEAR = "linear"
    EXPONENTIAL = "exponential"


def _parse_duration(duration: str | int) -> int:
    """Parse a duration string (e.g., '5s', '10m', '1h') to seconds.

    If already an integer, return as-is.
    """
    if isinstance(duration, int):
        return duration

    match = re.match(r"^(\d+)\s*([smh])?$", duration.strip().lower())
    if not match:
        raise ValueError(f"Invalid duration format: {duration}")

    value = int(match.group(1))
    unit = match.group(2) or "s"

    multipliers = {"s": 1, "m": 60, "h": 3600}
    return value * multipliers[unit]


class RetryConfig(BaseModel):
    """Configuration for retry logic."""

    max_attempts: int = Field(default=1, ge=1, description="Maximum number of attempts")
    backoff: BackoffStrategy = Field(
        default=BackoffStrategy.EXPONENTIAL, description="Backoff strategy: linear or exponential"
    )
    delay: str | int = Field(default="5s", description="Initial delay between retries")
    max_delay: str | int = Field(default="60s", description="Maximum delay between retries")

    @property
    def delay_seconds(self) -> int:
        """Get delay in seconds."""
        return _parse_duration(self.delay)

    @property
    def max_delay_seconds(self) -> int:
        """Get max delay in seconds."""
        return _parse_duration(self.max_delay)


class ErrorMode(str, Enum):
    """Error handling mode for pipeline steps."""

    FAIL = "fail"  # Stop pipeline on error
    CONTINUE = "continue"  # Continue pipeline on error


class CacheAction(str, Enum):
    """Cache action types."""

    RESTORE = "restore"
    SAVE = "save"
    RESTORE_AND_SAVE = "restore-and-save"


class StepCacheConfig(BaseModel):
    """Cache configuration for a pipeline step."""

    paths: list[str] = Field(
        default_factory=list,
        description="Paths to cache (relative to working directory)",
    )
    key: str = Field(
        default="",
        description="Cache key template (supports {{ hash('file') }} and {{ env.VAR }})",
    )
    action: CacheAction = Field(
        default=CacheAction.RESTORE_AND_SAVE,
        description="Cache action: restore, save, or restore-and-save",
    )


class CacheConfig(BaseModel):
    """Global cache configuration."""

    backend: str = Field(
        default="local",
        description="Cache backend: local or s3",
    )
    local_path: Path | None = Field(
        default=None,
        description="Local cache directory (default: ~/.relay/cache)",
    )
    s3_bucket: str | None = Field(
        default=None,
        description="S3 bucket name",
    )
    s3_endpoint: str | None = Field(
        default=None,
        description="S3 endpoint URL (for MinIO)",
    )
    s3_region: str | None = Field(
        default=None,
        description="S3 region",
    )
    s3_access_key: str | None = Field(
        default=None,
        description="S3 access key",
    )
    s3_secret_key: str | None = Field(
        default=None,
        description="S3 secret key",
    )
    s3_prefix: str = Field(
        default="relay-cache/",
        description="S3 key prefix",
    )


class AgentConfig(BaseModel):
    """Configuration for an AI agent."""

    command: str = Field(description="Command to run the agent")
    args: list[str] = Field(default_factory=list, description="Default arguments")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    timeout: int = Field(default=300, description="Timeout in seconds")


class ParallelStepConfig(BaseModel):
    """Configuration for a parallel sub-step."""

    name: str = Field(description="Unique name for this parallel step")
    agent: str = Field(description="Agent to use")
    prompt: str = Field(description="Prompt/instructions")
    output: str | None = Field(default=None, description="Output file")


class StepConfig(BaseModel):
    """Configuration for a pipeline step."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(description="Unique name for this step")
    agent: str | None = Field(default=None, description="Agent to use (refers to agents config)")
    prompt: str | None = Field(default=None, description="Prompt/instructions for the agent")
    input: str | None = Field(default=None, description="Input file from previous step")
    output: str | None = Field(default=None, description="Output file to save")
    working_dir: Path | None = Field(default=None, description="Working directory for this step")
    continue_on_error: bool = Field(default=False, description="Continue if this step fails")
    on_error: ErrorMode = Field(default=ErrorMode.FAIL, description="Error handling mode")
    retry: RetryConfig | None = Field(default=None, description="Retry configuration")
    timeout: str | int | None = Field(default=None, description="Step timeout (e.g., '10m', '60s')")
    parallel: list[ParallelStepConfig] | None = Field(
        default=None, description="Parallel sub-steps"
    )
    parallel_strategy: str = Field(
        default="concat", description="How to merge parallel outputs: concat, json, first"
    )
    needs: list[str] = Field(
        default_factory=list, description="List of step names this step depends on"
    )
    if_: str | None = Field(
        default=None,
        validation_alias="if",
        description="Condition to evaluate before running this step",
    )
    cache: StepCacheConfig | None = Field(
        default=None, description="Cache configuration for this step"
    )

    @field_validator("working_dir")
    @classmethod
    def validate_working_dir(cls, v: Path | None) -> Path | None:
        if v is not None:
            return v.expanduser().resolve()
        return v

    @property
    def timeout_seconds(self) -> int | None:
        """Get timeout in seconds."""
        if self.timeout is None:
            return None
        return _parse_duration(self.timeout)

    def get_retry_config(self) -> RetryConfig:
        """Get retry config, returning defaults if not set."""
        return self.retry or RetryConfig()


class PipelineConfig(BaseModel):
    """Configuration for a pipeline."""

    name: str = Field(description="Pipeline name")
    description: str | None = Field(default=None, description="Pipeline description")
    template: str | None = Field(
        default=None, description="Template reference (e.g., 'python-project@1.0.0')"
    )
    steps: list[StepConfig] = Field(description="Steps to execute")
    cache: CacheConfig | None = Field(
        default=None, description="Cache configuration for this pipeline"
    )


def _default_agents() -> dict[str, AgentConfig]:
    """Default agent configurations."""
    return {
        "claude-code": AgentConfig(command="claude"),
        "opencode": AgentConfig(
            command="opencode",
            env={"PATH": "/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:/usr/sbin"}
        ),
        "opencode-run": AgentConfig(
            command="opencode",
            args=["run"],
            env={"PATH": "/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:/usr/sbin"}
        ),
        "oh-my-opencode": AgentConfig(command="oh-my-opencode"),
        "gemini": AgentConfig(
            command="gemini",
            env={"PATH": "/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:/usr/sbin"}
        ),
        "aider": AgentConfig(command="aider"),
        "codex": AgentConfig(command="codex"),
    }


class RelayConfig(BaseModel):
    """Root configuration for Relay."""

    agents: dict[str, AgentConfig] = Field(
        default_factory=_default_agents, description="Agent configurations"
    )
    pipelines: dict[str, list[str]] = Field(
        default_factory=dict, description="Named pipeline step sequences"
    )
    cache: CacheConfig = Field(
        default_factory=lambda: CacheConfig(backend="local"),
        description="Global cache configuration"
    )

    @field_validator("agents")
    @classmethod
    def merge_agents(cls, v: dict[str, AgentConfig]) -> dict[str, AgentConfig]:
        """Merge user agents with defaults."""
        defaults = _default_agents()
        defaults.update(v)
        return defaults


class StepErrorDetails(BaseModel):
    """Detailed error information for a step."""

    message: str = Field(description="Error message")
    stderr: str = Field(default="", description="Standard error output")
    returncode: int | None = Field(default=None, description="Command return code")
    suggestion: str = Field(default="", description="Actionable suggestion for fixing the error")


class StepResult(BaseModel):
    """Result of executing a pipeline step."""

    step_name: str
    success: bool
    output: str = ""
    error: str | None = None
    error_details: StepErrorDetails | None = None
    duration_ms: int = 0
    artifacts: list[Path] = Field(default_factory=list)
    attempts: int = Field(default=1, description="Number of attempts made")
    timed_out: bool = Field(default=False, description="Whether the step timed out")
