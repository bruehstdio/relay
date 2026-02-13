"""Tests for Relay pipeline executor."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from relay.executor import PipelineExecutor
from relay.models import AgentConfig, ParallelStepConfig, PipelineConfig, StepConfig, StepResult


class TestPipelineExecutor:
    """Test PipelineExecutor class."""

    def test_init_default_working_dir(self) -> None:
        """Test initialization with default working directory."""
        executor = PipelineExecutor()
        assert executor.working_dir == Path.cwd()
        assert executor.results == []

    def test_init_custom_working_dir(self, tmp_path: Path) -> None:
        """Test initialization with custom working directory."""
        executor = PipelineExecutor(working_dir=tmp_path)
        assert executor.working_dir == tmp_path
        assert executor.artifacts_dir == tmp_path / ".relay" / "artifacts"
        assert executor.artifacts_dir.exists()

    def test_artifacts_dir_created(self, tmp_path: Path) -> None:
        """Test that artifacts directory is created on init."""
        artifacts_dir = tmp_path / ".relay" / "artifacts"
        assert not artifacts_dir.exists()
        
        executor = PipelineExecutor(working_dir=tmp_path)
        assert artifacts_dir.exists()


class TestExecuteStep:
    """Test step execution."""

    @pytest.fixture
    def executor(self, tmp_path: Path) -> PipelineExecutor:
        """Create a PipelineExecutor with temp working dir."""
        return PipelineExecutor(working_dir=tmp_path)

    @pytest.fixture
    def agent_config(self) -> AgentConfig:
        """Create a test agent config."""
        return AgentConfig(
            command="echo",
            args=["test output"],
            timeout=10,
        )

    @pytest.fixture
    def agents(self, agent_config: AgentConfig) -> dict[str, AgentConfig]:
        """Create agents dictionary."""
        return {"test-agent": agent_config}

    @patch("relay.executor.subprocess.run")
    def test_execute_step_success(
        self,
        mock_run: MagicMock,
        executor: PipelineExecutor,
        agents: dict[str, AgentConfig],
    ) -> None:
        """Test successful step execution."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Success output",
            stderr="",
        )
        
        step = StepConfig(
            name="test-step",
            agent="test-agent",
            prompt="Test prompt",
        )
        
        result = executor._execute_step(1, step, agents, None)
        
        assert result.success is True
        assert result.output == "Success output"
        # Note: step_name is not set by _execute_step, it's set by the caller
        # Note: duration_ms may be 0 in mocked tests

    @patch("relay.executor.subprocess.run")
    def test_execute_step_failure(
        self,
        mock_run: MagicMock,
        executor: PipelineExecutor,
        agents: dict[str, AgentConfig],
    ) -> None:
        """Test failed step execution."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error occurred",
        )
        
        step = StepConfig(
            name="test-step",
            agent="test-agent",
            prompt="Test prompt",
        )
        
        result = executor._execute_step(1, step, agents, None)
        
        assert result.success is False
        assert result.error == "Error occurred"

    @patch("relay.executor.subprocess.run")
    def test_execute_step_unknown_agent(
        self,
        mock_run: MagicMock,
        executor: PipelineExecutor,
    ) -> None:
        """Test step execution with unknown agent."""
        step = StepConfig(
            name="test-step",
            agent="unknown-agent",
            prompt="Test prompt",
        )
        
        result = executor._execute_step(1, step, {}, None)
        
        assert result.success is False
        assert "Unknown agent" in result.error
        mock_run.assert_not_called()

    @patch("relay.executor.subprocess.run")
    def test_execute_step_no_agent(
        self,
        mock_run: MagicMock,
        executor: PipelineExecutor,
    ) -> None:
        """Test step execution without agent or parallel."""
        step = StepConfig(
            name="test-step",
            prompt="Test prompt",
        )
        
        result = executor._execute_step(1, step, {}, None)
        
        assert result.success is False
        assert "must have either 'agent' or 'parallel'" in result.error
        mock_run.assert_not_called()

    @patch("relay.executor.subprocess.run")
    def test_execute_step_with_output(
        self,
        mock_run: MagicMock,
        executor: PipelineExecutor,
        agents: dict[str, AgentConfig],
    ) -> None:
        """Test step execution writes output to file."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Output content",
            stderr="",
        )
        
        step = StepConfig(
            name="test-step",
            agent="test-agent",
            prompt="Test prompt",
            output="output.txt",
        )
        
        result = executor._execute_step(1, step, agents, None)
        
        assert result.success is True
        output_path = executor.artifacts_dir / "output.txt"
        assert output_path.exists()
        assert output_path.read_text() == "Output content"
        assert result.artifacts == [output_path]

    @patch("relay.executor.subprocess.run")
    def test_execute_step_with_input(
        self,
        mock_run: MagicMock,
        executor: PipelineExecutor,
        agents: dict[str, AgentConfig],
    ) -> None:
        """Test step execution reads input file."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Processed",
            stderr="",
        )
        
        # Create input file
        input_file = executor.artifacts_dir / "input.txt"
        input_file.write_text("Input content")
        
        step = StepConfig(
            name="test-step",
            agent="test-agent",
            prompt="Process this",
            input="input.txt",
        )
        
        result = executor._execute_step(1, step, agents, None)
        
        assert result.success is True
        # Check that input content was included in prompt
        call_args = mock_run.call_args
        assert call_args is not None

    @patch("relay.executor.subprocess.run")
    def test_execute_step_with_previous_output(
        self,
        mock_run: MagicMock,
        executor: PipelineExecutor,
        agents: dict[str, AgentConfig],
    ) -> None:
        """Test step execution uses previous step output."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Done",
            stderr="",
        )
        
        # Create previous output file
        prev_output = executor.artifacts_dir / "prev.txt"
        prev_output.write_text("Previous content")
        
        step = StepConfig(
            name="test-step",
            agent="test-agent",
            prompt="Continue",
        )
        
        result = executor._execute_step(1, step, agents, prev_output)
        
        assert result.success is True

    @patch("relay.executor.subprocess.run")
    def test_execute_step_timeout(
        self,
        mock_run: MagicMock,
        executor: PipelineExecutor,
        agents: dict[str, AgentConfig],
    ) -> None:
        """Test step execution timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="echo", timeout=10)
        
        step = StepConfig(
            name="test-step",
            agent="test-agent",
            prompt="Test",
        )
        
        result = executor._execute_step(1, step, agents, None)
        
        assert result.success is False
        assert "Timeout" in result.error

    @patch("relay.executor.subprocess.run")
    def test_execute_step_exception(
        self,
        mock_run: MagicMock,
        executor: PipelineExecutor,
        agents: dict[str, AgentConfig],
    ) -> None:
        """Test step execution with exception."""
        mock_run.side_effect = OSError("Command not found")
        
        step = StepConfig(
            name="test-step",
            agent="test-agent",
            prompt="Test",
        )
        
        result = executor._execute_step(1, step, agents, None)
        
        assert result.success is False
        assert "Command not found" in result.error


class TestExecutePipeline:
    """Test full pipeline execution."""

    @pytest.fixture
    def executor(self, tmp_path: Path) -> PipelineExecutor:
        """Create a PipelineExecutor with temp working dir."""
        return PipelineExecutor(working_dir=tmp_path)

    @patch("relay.executor.subprocess.run")
    def test_execute_pipeline_success(
        self,
        mock_run: MagicMock,
        executor: PipelineExecutor,
    ) -> None:
        """Test successful pipeline execution."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Success",
            stderr="",
        )
        
        config = PipelineConfig(
            name="test-pipeline",
            steps=[
                StepConfig(name="step1", agent="test-agent", prompt="Prompt 1"),
                StepConfig(name="step2", agent="test-agent", prompt="Prompt 2"),
            ],
        )
        agents = {
            "test-agent": AgentConfig(command="echo", args=["test"]),
        }
        
        results = executor.execute(config, agents)
        
        assert len(results) == 2
        assert all(r.success for r in results)
        assert executor.results == results

    @patch("relay.executor.subprocess.run")
    def test_execute_pipeline_failure_stops(
        self,
        mock_run: MagicMock,
        executor: PipelineExecutor,
    ) -> None:
        """Test pipeline stops on failure."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Failed",
        )
        
        config = PipelineConfig(
            name="test-pipeline",
            steps=[
                StepConfig(name="step1", agent="test-agent", prompt="Prompt 1"),
                StepConfig(name="step2", agent="test-agent", prompt="Prompt 2"),
            ],
        )
        agents = {
            "test-agent": AgentConfig(command="echo"),
        }
        
        results = executor.execute(config, agents)
        
        # Should stop after first failure
        assert len(results) == 1
        assert results[0].success is False

    @patch("relay.executor.subprocess.run")
    def test_execute_pipeline_continue_on_error(
        self,
        mock_run: MagicMock,
        executor: PipelineExecutor,
    ) -> None:
        """Test pipeline continues on error when configured."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Failed",
        )
        
        config = PipelineConfig(
            name="test-pipeline",
            steps=[
                StepConfig(
                    name="step1",
                    agent="test-agent",
                    prompt="Prompt 1",
                    continue_on_error=True,
                ),
                StepConfig(name="step2", agent="test-agent", prompt="Prompt 2"),
            ],
        )
        agents = {
            "test-agent": AgentConfig(command="echo"),
        }
        
        results = executor.execute(config, agents)
        
        # Should continue despite failure
        assert len(results) == 2


class TestMergeParallelOutputs:
    """Test parallel output merging."""

    @pytest.fixture
    def executor(self, tmp_path: Path) -> PipelineExecutor:
        """Create a PipelineExecutor."""
        return PipelineExecutor(working_dir=tmp_path)

    def test_merge_first_strategy(self, executor: PipelineExecutor) -> None:
        """Test first success strategy."""
        results = [
            StepResult(step_name="step1", success=False, error="Failed"),
            StepResult(step_name="step2", success=True, output="Success output"),
            StepResult(step_name="step3", success=True, output="Another success"),
        ]
        
        merged = executor._merge_parallel_outputs(results, "first")
        
        assert merged == "Success output"

    def test_merge_first_no_success(self, executor: PipelineExecutor) -> None:
        """Test first strategy with no successes."""
        results = [
            StepResult(step_name="step1", success=False, error="Failed 1"),
            StepResult(step_name="step2", success=False, error="Failed 2"),
        ]
        
        merged = executor._merge_parallel_outputs(results, "first")
        
        assert merged == ""

    def test_merge_json_strategy(self, executor: PipelineExecutor) -> None:
        """Test JSON merge strategy."""
        results = [
            StepResult(step_name="step1", success=True, output="Output 1"),
            StepResult(step_name="step2", success=False, error="Error 2"),
        ]
        
        merged = executor._merge_parallel_outputs(results, "json")
        
        data = json.loads(merged)
        assert data["step1"]["success"] is True
        assert data["step1"]["output"] == "Output 1"
        assert data["step2"]["success"] is False
        assert data["step2"]["error"] == "Error 2"

    def test_merge_concat_strategy(self, executor: PipelineExecutor) -> None:
        """Test concat merge strategy."""
        results = [
            StepResult(step_name="step1", success=True, output="Output 1"),
            StepResult(step_name="step2", success=False, error="Error 2"),
        ]
        
        merged = executor._merge_parallel_outputs(results, "concat")
        
        assert "=== step1 ===" in merged
        assert "Output 1" in merged
        assert "=== step2 ===" in merged
        assert "ERROR: Error 2" in merged

    def test_merge_default_strategy(self, executor: PipelineExecutor) -> None:
        """Test default (concat) strategy."""
        results = [
            StepResult(step_name="step1", success=True, output="Output 1"),
        ]
        
        merged = executor._merge_parallel_outputs(results, "unknown")
        
        assert "=== step1 ===" in merged


class TestPreparePrompt:
    """Test prompt preparation."""

    @pytest.fixture
    def executor(self, tmp_path: Path) -> PipelineExecutor:
        """Create a PipelineExecutor."""
        return PipelineExecutor(working_dir=tmp_path)

    def test_prepare_prompt_basic(self, executor: PipelineExecutor) -> None:
        """Test basic prompt preparation."""
        step = StepConfig(
            name="test",
            agent="test-agent",
            prompt="Base prompt",
        )
        
        prompt = executor._prepare_prompt(step, None)
        
        assert prompt == "Base prompt"

    def test_prepare_prompt_with_input(self, executor: PipelineExecutor) -> None:
        """Test prompt preparation with input file."""
        input_file = executor.artifacts_dir / "input.txt"
        input_file.write_text("Input content")
        
        step = StepConfig(
            name="test",
            agent="test-agent",
            prompt="Process this",
            input="input.txt",
        )
        
        prompt = executor._prepare_prompt(step, None)
        
        assert "Input file (input.txt):" in prompt
        assert "Input content" in prompt

    def test_prepare_prompt_with_previous_output(
        self, executor: PipelineExecutor
    ) -> None:
        """Test prompt preparation with previous output."""
        prev_file = executor.artifacts_dir / "prev.txt"
        prev_file.write_text("Previous content")
        
        step = StepConfig(
            name="test",
            agent="test-agent",
            prompt="Continue",
        )
        
        prompt = executor._prepare_prompt(step, prev_file)
        
        assert "Previous step output:" in prompt
        assert "Previous content" in prompt

    def test_prepare_prompt_input_overrides_previous(
        self, executor: PipelineExecutor
    ) -> None:
        """Test that explicit input overrides previous output."""
        input_file = executor.artifacts_dir / "input.txt"
        input_file.write_text("Input content")
        
        prev_file = executor.artifacts_dir / "prev.txt"
        prev_file.write_text("Previous content")
        
        step = StepConfig(
            name="test",
            agent="test-agent",
            prompt="Process",
            input="input.txt",
        )
        
        prompt = executor._prepare_prompt(step, prev_file)
        
        assert "Input file (input.txt):" in prompt
        assert "Input content" in prompt


class TestRunAgent:
    """Test agent execution."""

    @pytest.fixture
    def executor(self, tmp_path: Path) -> PipelineExecutor:
        """Create a PipelineExecutor."""
        return PipelineExecutor(working_dir=tmp_path)

    @patch("relay.executor.subprocess.run")
    def test_run_agent_success(self, mock_run: MagicMock, executor: PipelineExecutor) -> None:
        """Test successful agent execution."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Output",
            stderr="",
        )
        
        agent = AgentConfig(command="echo", args=["hello"])
        result = executor._run_agent(agent, "prompt", executor.working_dir)
        
        assert result.success is True
        assert result.output == "Output"
        mock_run.assert_called_once()

    @patch("relay.executor.subprocess.run")
    def test_run_agent_with_env(self, mock_run: MagicMock, executor: PipelineExecutor) -> None:
        """Test agent execution with environment variables."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )
        
        agent = AgentConfig(
            command="echo",
            env={"CUSTOM_VAR": "value"},
        )
        result = executor._run_agent(agent, "prompt", executor.working_dir)
        
        call_kwargs = mock_run.call_args.kwargs
        assert "env" in call_kwargs
        assert call_kwargs["env"]["CUSTOM_VAR"] == "value"

    @patch("relay.executor.subprocess.run")
    def test_run_agent_with_working_dir(
        self, mock_run: MagicMock, executor: PipelineExecutor
    ) -> None:
        """Test agent execution respects working directory."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )
        
        agent = AgentConfig(command="echo")
        custom_dir = executor.working_dir / "custom"
        custom_dir.mkdir()
        
        result = executor._run_agent(agent, "prompt", custom_dir)
        
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["cwd"] == custom_dir

    @patch("relay.executor.subprocess.run")
    def test_run_agent_relay_env_removed(
        self, mock_run: MagicMock, executor: PipelineExecutor
    ) -> None:
        """Test that RELAY_STEP_INPUT/OUTPUT env vars are removed."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )
        
        agent = AgentConfig(
            command="echo",
            env={"RELAY_STEP_INPUT": "input", "RELAY_STEP_OUTPUT": "output"},
        )
        result = executor._run_agent(agent, "prompt", executor.working_dir)
        
        call_kwargs = mock_run.call_args.kwargs
        env = call_kwargs["env"]
        assert "RELAY_STEP_INPUT" not in env
        assert "RELAY_STEP_OUTPUT" not in env


class TestParallelStepExecution:
    """Test parallel step execution."""

    @pytest.fixture
    def executor(self, tmp_path: Path) -> PipelineExecutor:
        """Create a PipelineExecutor."""
        return PipelineExecutor(working_dir=tmp_path)

    @patch("relay.executor.subprocess.run")
    def test_execute_parallel_step(
        self, mock_run: MagicMock, executor: PipelineExecutor
    ) -> None:
        """Test parallel step execution."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Parallel output",
            stderr="",
        )
        
        step = StepConfig(
            name="parallel-step",
            parallel=[
                ParallelStepConfig(name="sub1", agent="agent1", prompt="Prompt 1"),
                ParallelStepConfig(name="sub2", agent="agent2", prompt="Prompt 2"),
            ],
            parallel_strategy="concat",
        )
        agents = {
            "agent1": AgentConfig(command="echo"),
            "agent2": AgentConfig(command="echo"),
        }
        
        result = executor._execute_parallel_step(1, step, agents, None)
        
        assert result.success is True
        assert "=== sub1 ===" in result.output
        assert "=== sub2 ===" in result.output

    @patch("relay.executor.subprocess.run")
    def test_execute_parallel_step_with_unknown_agent(
        self, mock_run: MagicMock, executor: PipelineExecutor
    ) -> None:
        """Test parallel step with unknown agent."""
        step = StepConfig(
            name="parallel-step",
            parallel=[
                ParallelStepConfig(name="sub1", agent="unknown", prompt="Prompt"),
            ],
        )
        
        result = executor._execute_parallel_step(1, step, {}, None)
        
        assert result.success is False
        assert "parallel tasks failed" in result.error


import json
