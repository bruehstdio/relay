"""Tests for Relay output formatting."""

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import pytest

from relay.models import PipelineConfig, StepConfig, StepResult
from relay.output_formatter import (
    OutputFormat,
    OutputFormatter,
    PipelineResult,
    create_pipeline_result,
)


class TestOutputFormat:
    """Test OutputFormat enum."""

    def test_format_values(self) -> None:
        """Test output format enum values."""
        assert OutputFormat.CONSOLE == "console"
        assert OutputFormat.JSON == "json"
        assert OutputFormat.JUNIT == "junit"
        assert OutputFormat.MARKDOWN == "markdown"


class TestPipelineResult:
    """Test PipelineResult dataclass."""

    def test_basic_creation(self) -> None:
        """Test creating a basic PipelineResult."""
        step = StepResult(
            step_name="test",
            success=True,
            output="output",
            duration_ms=100,
        )
        result = PipelineResult(
            pipeline="test-pipeline",
            status="success",
            duration=1.5,
            steps=[step],
        )
        
        assert result.pipeline == "test-pipeline"
        assert result.status == "success"
        assert result.duration == 1.5
        assert len(result.steps) == 1
        assert result.timestamp is not None

    def test_timestamp_auto_set(self) -> None:
        """Test that timestamp is auto-set if not provided."""
        result = PipelineResult(
            pipeline="test",
            status="success",
            duration=1.0,
            steps=[],
        )
        
        assert result.timestamp is not None
        assert isinstance(result.timestamp, datetime)

    def test_timestamp_can_be_set(self) -> None:
        """Test that timestamp can be explicitly set."""
        ts = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = PipelineResult(
            pipeline="test",
            status="success",
            duration=1.0,
            steps=[],
            timestamp=ts,
        )
        
        assert result.timestamp == ts


class TestOutputFormatter:
    """Test OutputFormatter class."""

    @pytest.fixture
    def sample_result(self) -> PipelineResult:
        """Create a sample pipeline result."""
        steps = [
            StepResult(
                step_name="step1",
                success=True,
                output="Step 1 output",
                duration_ms=100,
            ),
            StepResult(
                step_name="step2",
                success=False,
                output="",
                error="Something went wrong",
                duration_ms=200,
            ),
        ]
        return PipelineResult(
            pipeline="test-pipeline",
            status="partial",
            duration=0.5,
            steps=steps,
            timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        )

    def test_format_console(self, sample_result: PipelineResult) -> None:
        """Test console formatting."""
        formatter = OutputFormatter()
        output = formatter.format(sample_result, OutputFormat.CONSOLE)
        
        assert "Pipeline: test-pipeline" in output
        assert "Status: partial" in output
        assert "Duration: 0.50s" in output
        assert "Steps: 2" in output

    def test_format_json(self, sample_result: PipelineResult) -> None:
        """Test JSON formatting."""
        formatter = OutputFormatter()
        output = formatter.format(sample_result, OutputFormat.JSON)
        
        data = json.loads(output)
        assert data["pipeline"] == "test-pipeline"
        assert data["status"] == "partial"
        assert data["duration"] == 0.5
        assert len(data["steps"]) == 2
        assert data["steps"][0]["name"] == "step1"
        assert data["steps"][0]["status"] == "success"
        assert data["steps"][1]["name"] == "step2"
        assert data["steps"][1]["status"] == "failed"
        assert data["steps"][1]["error"] == "Something went wrong"

    def test_format_json_with_timestamp(self, sample_result: PipelineResult) -> None:
        """Test JSON formatting includes timestamp."""
        formatter = OutputFormatter()
        output = formatter.format(sample_result, OutputFormat.JSON)
        
        data = json.loads(output)
        assert "timestamp" in data
        assert "2024-01-15" in data["timestamp"]

    def test_format_junit(self, sample_result: PipelineResult) -> None:
        """Test JUnit XML formatting."""
        formatter = OutputFormatter()
        output = formatter.format(sample_result, OutputFormat.JUNIT)
        
        # Parse XML
        root = ET.fromstring(output)
        
        assert root.tag == "testsuites"
        testsuite = root.find("testsuite")
        assert testsuite is not None
        assert testsuite.get("name") == "test-pipeline"
        assert testsuite.get("tests") == "2"
        assert testsuite.get("failures") == "1"
        
        testcases = testsuite.findall("testcase")
        assert len(testcases) == 2
        
        # First test case should not have failure
        assert testcases[0].find("failure") is None
        # Second test case should have failure
        assert testcases[1].find("failure") is not None

    def test_format_junit_success_only(self) -> None:
        """Test JUnit formatting with all successful steps."""
        steps = [
            StepResult(
                step_name="step1",
                success=True,
                output="Output",
                duration_ms=100,
            ),
        ]
        result = PipelineResult(
            pipeline="success-pipeline",
            status="success",
            duration=0.5,
            steps=steps,
        )
        
        formatter = OutputFormatter()
        output = formatter.format(result, OutputFormat.JUNIT)
        
        root = ET.fromstring(output)
        testsuite = root.find("testsuite")
        assert testsuite.get("failures") == "0"

    def test_format_markdown(self, sample_result: PipelineResult) -> None:
        """Test Markdown formatting."""
        formatter = OutputFormatter()
        output = formatter.format(sample_result, OutputFormat.MARKDOWN)
        
        assert "# test-pipeline - Pipeline Report" in output
        assert "⚠️ PARTIAL" in output
        assert "| Step | Status | Duration |" in output
        assert "| step1 | ✅ success | 0.10s |" in output
        assert "| step2 | ❌ failed | 0.20s |" in output
        assert "## Details" in output
        assert "Something went wrong" in output

    def test_format_markdown_all_success(self) -> None:
        """Test Markdown formatting with all success."""
        steps = [
            StepResult(
                step_name="step1",
                success=True,
                output="Output",
                duration_ms=100,
            ),
        ]
        result = PipelineResult(
            pipeline="success-pipeline",
            status="success",
            duration=0.5,
            steps=steps,
        )
        
        formatter = OutputFormatter()
        output = formatter.format(result, OutputFormat.MARKDOWN)
        
        assert "✅ SUCCESS" in output

    def test_format_markdown_all_failed(self) -> None:
        """Test Markdown formatting with all failed."""
        steps = [
            StepResult(
                step_name="step1",
                success=False,
                error="Failed",
                duration_ms=100,
            ),
        ]
        result = PipelineResult(
            pipeline="failed-pipeline",
            status="failed",
            duration=0.5,
            steps=steps,
        )
        
        formatter = OutputFormatter()
        output = formatter.format(result, OutputFormat.MARKDOWN)
        
        assert "❌ FAILED" in output

    def test_format_markdown_truncates_long_output(self) -> None:
        """Test that long output is truncated in Markdown."""
        steps = [
            StepResult(
                step_name="step1",
                success=True,
                output="x" * 3000,
                duration_ms=100,
            ),
        ]
        result = PipelineResult(
            pipeline="test",
            status="success",
            duration=0.5,
            steps=steps,
        )
        
        formatter = OutputFormatter()
        output = formatter.format(result, OutputFormat.MARKDOWN)
        
        assert "..." in output
        assert len(output) < 4000

    def test_format_writes_to_file(self, sample_result: PipelineResult, tmp_path: Path) -> None:
        """Test that format writes to file when path provided."""
        formatter = OutputFormatter()
        output_path = tmp_path / "output.json"
        
        output = formatter.format(
            sample_result,
            OutputFormat.JSON,
            output_path=output_path,
        )
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "test-pipeline" in content
        assert content == output

    def test_invalid_format_defaults_to_console(self, sample_result: PipelineResult) -> None:
        """Test that invalid format defaults to console."""
        formatter = OutputFormatter()
        # Access private method directly with invalid format
        formatter_func = formatter._get_formatter("invalid")  # type: ignore
        output = formatter_func(sample_result)
        
        assert "Pipeline: test-pipeline" in output

    def test_junit_with_system_out(self) -> None:
        """Test JUnit formatting includes system-out."""
        steps = [
            StepResult(
                step_name="step1",
                success=True,
                output="Standard output content",
                duration_ms=100,
            ),
        ]
        result = PipelineResult(
            pipeline="test",
            status="success",
            duration=0.5,
            steps=steps,
        )
        
        formatter = OutputFormatter()
        output = formatter.format(result, OutputFormat.JUNIT)
        
        root = ET.fromstring(output)
        testcase = root.find(".//testcase")
        system_out = testcase.find("system-out")
        assert system_out is not None
        assert system_out.text == "Standard output content"


class TestCreatePipelineResult:
    """Test create_pipeline_result function."""

    def test_create_success_result(self) -> None:
        """Test creating result for successful pipeline."""
        config = PipelineConfig(
            name="test-pipeline",
            steps=[
                StepConfig(name="step1", agent="test"),
                StepConfig(name="step2", agent="test"),
            ],
        )
        step_results = [
            StepResult(step_name="step1", success=True, duration_ms=100),
            StepResult(step_name="step2", success=True, duration_ms=200),
        ]
        
        result = create_pipeline_result(config, step_results, 1.5)
        
        assert result.pipeline == "test-pipeline"
        assert result.status == "success"
        assert result.duration == 1.5
        assert len(result.steps) == 2

    def test_create_failed_result(self) -> None:
        """Test creating result for failed pipeline."""
        config = PipelineConfig(
            name="test-pipeline",
            steps=[
                StepConfig(name="step1", agent="test"),
            ],
        )
        step_results = [
            StepResult(step_name="step1", success=False, error="Failed"),
        ]
        
        result = create_pipeline_result(config, step_results, 0.5)
        
        assert result.status == "failed"

    def test_create_partial_result(self) -> None:
        """Test creating result for partially successful pipeline."""
        config = PipelineConfig(
            name="test-pipeline",
            steps=[
                StepConfig(name="step1", agent="test"),
                StepConfig(name="step2", agent="test"),
            ],
        )
        step_results = [
            StepResult(step_name="step1", success=True, duration_ms=100),
            StepResult(step_name="step2", success=False, error="Failed"),
        ]
        
        result = create_pipeline_result(config, step_results, 1.0)
        
        assert result.status == "partial"
