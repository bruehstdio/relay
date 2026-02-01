"""Tests for parallel step execution."""

from pathlib import Path

import pytest

from relay.models import ParallelStepConfig, StepConfig


class TestParallelStepConfig:
    """Test ParallelStepConfig model."""

    def test_basic_parallel_step(self) -> None:
        """Test creating a parallel step config."""
        step = ParallelStepConfig(
            name="security-check",
            agent="claude-code",
            prompt="Check for security issues",
            output="security.txt",
        )
        assert step.name == "security-check"
        assert step.agent == "claude-code"
        assert step.output == "security.txt"


class TestStepConfigParallel:
    """Test StepConfig with parallel sub-steps."""

    def test_step_with_parallel(self) -> None:
        """Test step with parallel sub-steps."""
        step = StepConfig(
            name="analysis",
            parallel=[
                ParallelStepConfig(
                    name="security-check",
                    agent="claude-code",
                    prompt="Check security",
                    output="security.txt",
                ),
                ParallelStepConfig(
                    name="performance-check",
                    agent="opencode",
                    prompt="Check performance",
                    output="performance.txt",
                ),
            ],
            parallel_strategy="concat",
            output="analysis.txt",
        )
        assert len(step.parallel) == 2
        assert step.parallel_strategy == "concat"

    def test_parallel_strategy_options(self) -> None:
        """Test different parallel strategies."""
        step_concat = StepConfig(
            name="test",
            parallel=[],
            parallel_strategy="concat",
        )
        step_json = StepConfig(
            name="test",
            parallel=[],
            parallel_strategy="json",
        )
        step_first = StepConfig(
            name="test",
            parallel=[],
            parallel_strategy="first",
        )
        assert step_concat.parallel_strategy == "concat"
        assert step_json.parallel_strategy == "json"
        assert step_first.parallel_strategy == "first"

    def test_step_requires_agent_or_parallel(self) -> None:
        """Step should have either agent or parallel defined."""
        # This is validated at runtime, but we can check the model allows it
        step = StepConfig(name="test")
        assert step.agent is None
        assert step.parallel is None
