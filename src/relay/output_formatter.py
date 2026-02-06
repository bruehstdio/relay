"""Output formatters for Relay pipeline results."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from relay.models import PipelineConfig, StepResult


class OutputFormat(str, Enum):
    """Output format options."""

    CONSOLE = "console"
    JSON = "json"
    JUNIT = "junit"
    MARKDOWN = "markdown"


@dataclass
class PipelineResult:
    """Complete pipeline execution result."""

    pipeline: str
    status: str  # success, failed, partial
    duration: float  # seconds
    steps: list[StepResult]
    timestamp: datetime | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class OutputFormatter:
    """Formats pipeline execution results in various output formats."""

    def format(
        self,
        result: PipelineResult,
        format_type: OutputFormat,
        output_path: Path | None = None,
    ) -> str:
        """Format pipeline result in the specified format.

        Args:
            result: The pipeline execution result
            format_type: The output format to use
            output_path: Optional path to write the output to

        Returns:
            The formatted output string
        """
        formatter = self._get_formatter(format_type)
        output = formatter(result)

        if output_path:
            output_path.write_text(output)

        return output

    def _get_formatter(self, format_type: OutputFormat) -> callable:
        """Get the formatter function for the given format type."""
        formatters = {
            OutputFormat.CONSOLE: self._format_console,
            OutputFormat.JSON: self._format_json,
            OutputFormat.JUNIT: self._format_junit,
            OutputFormat.MARKDOWN: self._format_markdown,
        }
        return formatters.get(format_type, self._format_console)

    def _format_console(self, result: PipelineResult) -> str:
        """Format result for console output (rich text)."""
        # Console output is handled by the executor's rich console
        # This returns a simple text summary
        lines = [
            f"Pipeline: {result.pipeline}",
            f"Status: {result.status}",
            f"Duration: {result.duration:.2f}s",
            f"Steps: {len(result.steps)}",
        ]
        return "\n".join(lines)

    def _format_json(self, result: PipelineResult) -> str:
        """Format result as JSON."""
        data = {
            "pipeline": result.pipeline,
            "status": result.status,
            "duration": round(result.duration, 3),
            "timestamp": result.timestamp.isoformat() if result.timestamp else None,
            "steps": [
                {
                    "name": step.step_name,
                    "status": "success" if step.success else "failed",
                    "duration": round(step.duration_ms / 1000, 3),
                    "exit_code": 0 if step.success else 1,
                    "output": step.output if step.output else None,
                    "error": step.error,
                }
                for step in result.steps
            ],
        }
        return json.dumps(data, indent=2)

    def _format_junit(self, result: PipelineResult) -> str:
        """Format result as JUnit XML for CI integration."""
        testsuites = ET.Element("testsuites")
        testsuite = ET.SubElement(
            testsuites,
            "testsuite",
            {
                "name": result.pipeline,
                "tests": str(len(result.steps)),
                "failures": str(sum(1 for s in result.steps if not s.success)),
                "time": str(round(result.duration, 3)),
                "timestamp": result.timestamp.isoformat() if result.timestamp else "",
            },
        )

        for step in result.steps:
            testcase = ET.SubElement(
                testsuite,
                "testcase",
                {
                    "name": step.step_name,
                    "time": str(round(step.duration_ms / 1000, 3)),
                },
            )

            if not step.success:
                failure = ET.SubElement(
                    testcase,
                    "failure",
                    {"message": step.error or "Step failed"},
                )
                failure.text = step.error or "Step execution failed"

            if step.output:
                system_out = ET.SubElement(testcase, "system-out")
                system_out.text = step.output

        # Pretty print XML
        self._indent_xml(testsuites)
        return '<?xml version="1.0"?>\n' + ET.tostring(testsuites, encoding="unicode")

    def _format_markdown(self, result: PipelineResult) -> str:
        """Format result as Markdown summary."""
        status_icon = "✅" if result.status == "success" else "❌" if result.status == "failed" else "⚠️"

        lines = [
            f"# {result.pipeline} - Pipeline Report",
            "",
            f"**Status:** {status_icon} {result.status.upper()}",
            f"**Duration:** {result.duration:.2f}s",
            f"**Steps:** {len(result.steps)} total, {sum(1 for s in result.steps if s.success)} passed, {sum(1 for s in result.steps if not s.success)} failed",
            f"**Timestamp:** {result.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') if result.timestamp else 'N/A'}",
            "",
            "## Steps",
            "",
            "| Step | Status | Duration |",
            "|------|--------|----------|",
        ]

        for step in result.steps:
            icon = "✅" if step.success else "❌"
            status_text = "success" if step.success else "failed"
            duration = f"{step.duration_ms / 1000:.2f}s"
            lines.append(f"| {step.step_name} | {icon} {status_text} | {duration} |")

        lines.extend([
            "",
            "## Details",
            "",
        ])

        for step in result.steps:
            lines.append(f"### {step.step_name}")
            lines.append("")
            lines.append(f"- **Status:** {'✅ Success' if step.success else '❌ Failed'}")
            lines.append(f"- **Duration:** {step.duration_ms / 1000:.2f}s")

            if step.error:
                lines.append("")
                lines.append("**Error:**")
                lines.append("```")
                lines.append(step.error)
                lines.append("```")

            if step.output:
                lines.append("")
                lines.append("**Output:**")
                lines.append("```")
                # Truncate long output
                output = step.output[:2000] + "..." if len(step.output) > 2000 else step.output
                lines.append(output)
                lines.append("```")

            lines.append("")

        return "\n".join(lines)

    def _indent_xml(self, elem: ET.Element, level: int = 0) -> None:
        """Add pretty-print indentation to XML elements."""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():  # type: ignore
                child.tail = i  # type: ignore
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i


def create_pipeline_result(
    config: PipelineConfig,
    step_results: list[StepResult],
    total_duration: float,
) -> PipelineResult:
    """Create a PipelineResult from execution data.

    Args:
        config: The pipeline configuration
        step_results: List of step execution results
        total_duration: Total execution time in seconds

    Returns:
        A PipelineResult object
    """
    successful = sum(1 for r in step_results if r.success)
    total = len(step_results)

    if successful == total:
        status = "success"
    elif successful == 0:
        status = "failed"
    else:
        status = "partial"

    return PipelineResult(
        pipeline=config.name,
        status=status,
        duration=total_duration,
        steps=step_results,
    )
