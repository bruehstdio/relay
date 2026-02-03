"""Pipeline execution engine."""

from __future__ import annotations

import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.status import Status

from relay.models import AgentConfig, PipelineConfig, StepConfig, StepResult

console = Console()

console = Console()


class PipelineExecutor:
    """Executes pipelines with multiple agent steps."""

    def __init__(self, working_dir: Path | None = None) -> None:
        self.working_dir = working_dir or Path.cwd()
        self.artifacts_dir = self.working_dir / ".relay" / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.results: list[StepResult] = []

    def execute(
        self, config: PipelineConfig, agents: dict[str, AgentConfig]
    ) -> list[StepResult]:
        """Execute a pipeline configuration."""
        console.print(Panel.fit(f"[bold blue]Pipeline: {config.name}[/bold blue]"))
        if config.description:
            console.print(f"[dim]{config.description}[/dim]\n")

        self.results = []
        previous_output: Path | None = None

        for i, step in enumerate(config.steps, 1):
            result = self._execute_step(i, step, agents, previous_output)
            self.results.append(result)

            if not result.success and not step.continue_on_error:
                console.print(f"\n[bold red]✗ Pipeline failed at step {i}: {step.name}[/bold red]")
                break

            if result.artifacts:
                previous_output = result.artifacts[0]

        self._print_summary()
        return self.results

    def _execute_step(
        self,
        step_num: int,
        step: StepConfig,
        agents: dict[str, AgentConfig],
        previous_output: Path | None,
    ) -> StepResult:
        """Execute a single pipeline step (sequential or parallel)."""
        # Handle parallel steps
        if step.parallel:
            return self._execute_parallel_step(step_num, step, agents, previous_output)

        # Handle regular sequential step
        if not step.agent:
            return StepResult(
                step_name=step.name,
                success=False,
                error="Step must have either 'agent' or 'parallel' defined",
            )

        agent_config = agents.get(step.agent)
        if not agent_config:
            return StepResult(
                step_name=step.name,
                success=False,
                error=f"Unknown agent: {step.agent}",
            )

        import time

        status_msg = f"[bold cyan]Step {step_num}/{len(self.results) + 1}:[/bold cyan] {step.name}"
        with Status(status_msg, console=console) as status:
            start_time = time.time()

            # Prepare prompt with context
            prompt = self._prepare_prompt(step, previous_output)

            result = self._run_agent(agent_config, prompt, step.working_dir or self.working_dir)

            duration_ms = int((time.time() - start_time) * 1000)

            # Write output to file if specified
            artifacts: list[Path] = []
            if step.output and result.success:
                output_path = self.artifacts_dir / step.output
                output_path.write_text(result.output)
                artifacts.append(output_path)
                result.artifacts = artifacts

            result.duration_ms = duration_ms

            status_color = "green" if result.success else "red"
            status_icon = "✓" if result.success else "✗"
            status.update(
                f"[bold {status_color}]{status_icon}[/bold {status_color}] "
                f"Step {step_num}: {step.name} ([dim]{duration_ms}ms[/dim])"
            )

            return result

    def _execute_parallel_step(
        self,
        step_num: int,
        step: StepConfig,
        agents: dict[str, AgentConfig],
        previous_output: Path | None,
    ) -> StepResult:
        """Execute parallel sub-steps concurrently."""
        import time

        start_time = time.time()
        parallel_steps = step.parallel or []

        console.print(
            f"[bold cyan]Step {step_num}/{len(self.results) + 1}:[/bold cyan] "
            f"{step.name} ([dim]{len(parallel_steps)} parallel tasks[/dim])"
        )

        # Prepare base prompt
        base_prompt = self._prepare_prompt(step, previous_output)

        # Execute parallel steps
        results: list[StepResult] = []
        with ThreadPoolExecutor(max_workers=len(parallel_steps)) as executor:
            futures = {}
            for parallel_step in parallel_steps:
                agent_config = agents.get(parallel_step.agent)
                if not agent_config:
                    results.append(StepResult(
                        step_name=parallel_step.name,
                        success=False,
                        error=f"Unknown agent: {parallel_step.agent}",
                    ))
                    continue

                # Combine base prompt with parallel step prompt
                if base_prompt:
                    full_prompt = f"{base_prompt}\n\n{parallel_step.prompt}"
                else:
                    full_prompt = parallel_step.prompt

                future = executor.submit(
                    self._run_agent,
                    agent_config,
                    full_prompt,
                    step.working_dir or self.working_dir
                )
                futures[future] = parallel_step

            for future in as_completed(futures):
                parallel_step = futures[future]
                try:
                    result = future.result()
                    result.step_name = parallel_step.name
                    results.append(result)
                    status_icon = "✓" if result.success else "✗"
                    status_color = "green" if result.success else "red"
                    msg = f"  [{status_color}]{status_icon}[/{status_color}] {parallel_step.name}"
                    console.print(msg)
                except Exception as e:
                    results.append(StepResult(
                        step_name=parallel_step.name,
                        success=False,
                        error=str(e),
                    ))
                    console.print(f"  [red]✗[/red] {parallel_step.name}: {e}")

        # Merge results based on strategy
        merged_output = self._merge_parallel_outputs(results, step.parallel_strategy)

        duration_ms = int((time.time() - start_time) * 1000)
        all_success = all(r.success for r in results)

        # Write merged output if specified
        artifacts: list[Path] = []
        if step.output and all_success:
            output_path = self.artifacts_dir / step.output
            output_path.write_text(merged_output)
            artifacts.append(output_path)

        return StepResult(
            step_name=step.name,
            success=all_success,
            output=merged_output,
            error=None if all_success else f"{sum(1 for r in results if not r.success)} "
            "parallel tasks failed",
            duration_ms=duration_ms,
            artifacts=artifacts,
        )

    def _run_agent(
        self,
        agent_config: AgentConfig,
        prompt: str,
        working_dir: Path,
    ) -> StepResult:
        """Run a single agent command."""
        cmd = [agent_config.command, *agent_config.args]

        # Set up environment
        env = os.environ.copy()
        env.update(agent_config.env)
        if "RELAY_STEP_INPUT" in env:
            del env["RELAY_STEP_INPUT"]
        if "RELAY_STEP_OUTPUT" in env:
            del env["RELAY_STEP_OUTPUT"]

        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=agent_config.timeout,
                cwd=working_dir,
                env=env,
            )

            success = result.returncode == 0
            return StepResult(
                step_name="",  # Will be set by caller
                success=success,
                output=result.stdout,
                error=result.stderr if not success else None,
                duration_ms=0,  # Will be set by caller
                artifacts=[],
            )

        except subprocess.TimeoutExpired:
            return StepResult(
                step_name="",
                success=False,
                error=f"Timeout after {agent_config.timeout}s",
                duration_ms=0,
                artifacts=[],
            )
        except Exception as e:
            return StepResult(
                step_name="",
                success=False,
                error=str(e),
                duration_ms=0,
                artifacts=[],
            )

    def _merge_parallel_outputs(self, results: list[StepResult], strategy: str) -> str:
        """Merge outputs from parallel steps based on strategy."""
        if strategy == "first":
            for result in results:
                if result.success and result.output:
                    return result.output
            return ""

        elif strategy == "json":
            outputs = {}
            for result in results:
                outputs[result.step_name] = {
                    "success": result.success,
                    "output": result.output,
                    "error": result.error,
                }
            return json.dumps(outputs, indent=2)

        else:  # concat (default)
            parts = []
            for result in results:
                parts.append(f"=== {result.step_name} ===")
                if result.success:
                    parts.append(result.output)
                else:
                    parts.append(f"ERROR: {result.error}")
                parts.append("")
            return "\n".join(parts)

    def _prepare_prompt(self, step: StepConfig, previous_output: Path | None) -> str:
        """Prepare the prompt for a step, including context from previous steps."""
        prompt = step.prompt or ""

        # Add input file content if specified
        if step.input:
            input_path = self.artifacts_dir / step.input
            if input_path.exists():
                content = input_path.read_text()
                prompt = f"Input file ({step.input}):\n```\n{content}\n```\n\n{prompt}"

        # Add previous step output if no explicit input
        elif previous_output and previous_output.exists():
            content = previous_output.read_text()
            prompt = f"Previous step output:\n```\n{content}\n```\n\n{prompt}"

        return prompt

    def _print_summary(self) -> None:
        """Print execution summary."""
        successful = sum(1 for r in self.results if r.success)
        total = len(self.results)
        total_time = sum(r.duration_ms for r in self.results)

        color = "green" if successful == total else "yellow" if successful > 0 else "red"

        console.print(
            f"\n[bold {color}]Pipeline complete:[/bold {color}] "
            f"{successful}/{total} steps succeeded"
        )
        console.print(f"[dim]Total time: {total_time}ms[/dim]")

        if any(r.error for r in self.results):
            console.print("\n[bold red]Errors:[/bold red]")
            for r in self.results:
                if r.error:
                    console.print(f"  [red]• {r.step_name}:[/red] {r.error}")
