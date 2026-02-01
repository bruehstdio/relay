"""Tests for environment variable interpolation."""

import os
from pathlib import Path

import pytest

from relay.config import _interpolate_env_vars, load_pipeline
from relay.models import PipelineConfig


class TestEnvVarInterpolation:
    """Test environment variable interpolation."""

    def test_interpolate_simple_var(self) -> None:
        """Test simple ${VAR} interpolation."""
        os.environ["TEST_VAR"] = "hello"
        result = _interpolate_env_vars("Value is ${TEST_VAR}")
        assert result == "Value is hello"

    def test_interpolate_with_default(self) -> None:
        """Test ${VAR:-default} syntax."""
        # When var is not set
        if "UNSET_VAR" in os.environ:
            del os.environ["UNSET_VAR"]
        result = _interpolate_env_vars("Value is ${UNSET_VAR:-default_value}")
        assert result == "Value is default_value"

        # When var is set
        os.environ["UNSET_VAR"] = "custom"
        result = _interpolate_env_vars("Value is ${UNSET_VAR:-default_value}")
        assert result == "Value is custom"
        del os.environ["UNSET_VAR"]

    def test_interpolate_nested_structure(self) -> None:
        """Test interpolation in nested dicts and lists."""
        os.environ["AGENT_NAME"] = "claude-code"
        os.environ["MODEL"] = "claude-3-5-sonnet"
        
        data = {
            "name": "test",
            "agents": {
                "default": "${AGENT_NAME}",
            },
            "steps": [
                {"agent": "${AGENT_NAME}", "model": "${MODEL}"},
            ],
        }
        
        result = _interpolate_env_vars(data)
        assert result["agents"]["default"] == "claude-code"
        assert result["steps"][0]["agent"] == "claude-code"
        assert result["steps"][0]["model"] == "claude-3-5-sonnet"

    def test_interpolate_non_string_unchanged(self) -> None:
        """Test that non-string values are unchanged."""
        result = _interpolate_env_vars(42)
        assert result == 42
        
        result = _interpolate_env_vars(True)
        assert result is True

    def test_pipeline_with_env_vars(self, tmp_path: Path) -> None:
        """Test loading pipeline with env var interpolation."""
        os.environ["PR_NUMBER"] = "42"
        os.environ["AGENT"] = "claude-code"
        
        pipeline_file = tmp_path / "test-pipeline.yml"
        pipeline_file.write_text("""
name: "PR Review #{PR_NUMBER}"
steps:
  - name: review
    agent: ${AGENT}
    prompt: "Review PR #{PR_NUMBER}"
""")
        
        pipeline = load_pipeline(pipeline_file)
        assert pipeline.name == "PR Review #42"
        assert pipeline.steps[0].agent == "claude-code"
        assert "42" in pipeline.steps[0].prompt
