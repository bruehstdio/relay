"""Pydantic models for Relay configuration and execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class AgentConfig(BaseModel):
    """Configuration for an AI agent."""

    command: str = Field(description="Command to run the agent")
    args: list[str] = Field(default_factory=list, description="Default arguments")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    timeout: int = Field(default=300, description="Timeout in seconds")


class StepConfig(BaseModel):
    """Configuration for a pipeline step."""

    name: str = Field(description="Unique name for this step")
    agent: str = Field(description="Agent to use (refers to agents config)")
    prompt: str = Field(description="Prompt/instructions for the agent")
    input: str | None = Field(default=None, description="Input file from previous step")
    output: str | None = Field(default=None, description="Output file to save")
    working_dir: Path | None = Field(default=None, description="Working directory for this step")
    continue_on_error: bool = Field(default=False, description="Continue if this step fails")

    @field_validator("working_dir")
    @classmethod
    def validate_working_dir(cls, v: Path | None) -> Path | None:
        if v is not None:
            return v.expanduser().resolve()
        return v


class PipelineConfig(BaseModel):
    """Configuration for a pipeline."""

    name: str = Field(description="Pipeline name")
    description: str | None = Field(default=None, description="Pipeline description")
    steps: list[StepConfig] = Field(description="Steps to execute")


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

    @field_validator("agents")
    @classmethod
    def merge_agents(cls, v: dict[str, AgentConfig]) -> dict[str, AgentConfig]:
        """Merge user agents with defaults."""
        defaults = _default_agents()
        defaults.update(v)
        return defaults


class StepResult(BaseModel):
    """Result of executing a pipeline step."""

    step_name: str
    success: bool
    output: str = ""
    error: str | None = None
    duration_ms: int = 0
    artifacts: list[Path] = Field(default_factory=list)
