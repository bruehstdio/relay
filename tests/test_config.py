"""Tests for Relay configuration loading."""

from pathlib import Path

import pytest

from relay.config import load_config, load_pipeline
from relay.models import AgentConfig, PipelineConfig, RelayConfig, StepConfig


class TestLoadConfig:
    """Test configuration loading."""

    def test_load_nonexistent_config_returns_defaults(self, tmp_path: Path) -> None:
        """Loading a non-existent config should return default agents."""
        config = load_config(tmp_path / "nonexistent.yml")
        assert isinstance(config, RelayConfig)
        assert "claude-code" in config.agents
        assert "opencode" in config.agents

    def test_default_agents_have_commands(self) -> None:
        """Default agents should have commands configured."""
        config = load_config(Path("/dev/null"))
        assert config.agents["claude-code"].command == "claude"
        assert config.agents["opencode"].command == "opencode"
        assert config.agents["aider"].command == "aider"
        assert config.agents["codex"].command == "codex"


class TestLoadPipeline:
    """Test pipeline configuration loading."""

    def test_load_simple_pipeline(self, tmp_path: Path) -> None:
        """Load a simple pipeline YAML file."""
        pipeline_file = tmp_path / "test-pipeline.yml"
        pipeline_file.write_text("""
name: "test-pipeline"
description: "A test pipeline"
steps:
  - name: step1
    agent: claude-code
    prompt: "Do something"
    output: result.txt
""")
        
        pipeline = load_pipeline(pipeline_file)
        assert isinstance(pipeline, PipelineConfig)
        assert pipeline.name == "test-pipeline"
        assert len(pipeline.steps) == 1
        assert pipeline.steps[0].name == "step1"

    def test_load_pipeline_with_input(self, tmp_path: Path) -> None:
        """Load pipeline with input from previous step."""
        pipeline_file = tmp_path / "test-pipeline.yml"
        pipeline_file.write_text("""
name: "chained-pipeline"
steps:
  - name: first
    agent: opencode
    prompt: "First step"
    output: first.txt
  - name: second
    agent: claude-code
    prompt: "Second step"
    input: first.txt
    output: second.txt
""")
        
        pipeline = load_pipeline(pipeline_file)
        assert len(pipeline.steps) == 2
        assert pipeline.steps[1].input == "first.txt"


class TestAgentConfig:
    """Test AgentConfig model."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        agent = AgentConfig(command="test-cmd")
        assert agent.command == "test-cmd"
        assert agent.args == []
        assert agent.env == {}
        assert agent.timeout == 300

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        agent = AgentConfig(
            command="custom",
            args=["--verbose", "--flag"],
            env={"KEY": "value"},
            timeout=600,
        )
        assert agent.args == ["--verbose", "--flag"]
        assert agent.env == {"KEY": "value"}
        assert agent.timeout == 600


class TestStepConfig:
    """Test StepConfig model."""

    def test_continue_on_error_default(self) -> None:
        """Test default value for continue_on_error."""
        step = StepConfig(
            name="test",
            agent="claude-code",
            prompt="Test prompt",
        )
        assert step.continue_on_error is False
