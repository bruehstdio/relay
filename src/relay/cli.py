"""Relay CLI - Chain AI coding agents like a CI pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from relay.config import find_config_file, load_config, load_pipeline
from relay.dashboard import run_dashboard, show_pipeline_status
from relay.executor import PipelineExecutor
from relay.models import PipelineConfig, RelayConfig

app = typer.Typer(
    name="relay",
    help="Chain AI coding agents like a CI pipeline",
    no_args_is_help=True,
)
console = Console()


@app.command()
def run(
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Pipeline configuration file"),
    ] = None,
    working_dir: Annotated[
        Path | None,
        typer.Option("--working-dir", "-w", help="Working directory"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", "-n", help="Show what would be executed"),
    ] = False,
) -> None:
    """Run a pipeline."""
    # Load global config
    global_config_path = find_config_file()
    if global_config_path:
        global_config = load_config(global_config_path)
    else:
        global_config = load_config(Path("/dev/null"))

    # Load pipeline config
    if config:
        pipeline = load_pipeline(config)
    else:
        # Try to find a pipeline file
        for name in ["pipeline.yml", "pipeline.yaml", "relay-pipeline.yml", "relay-pipeline.yaml"]:
            path = Path(name)
            if path.exists():
                pipeline = load_pipeline(path)
                break
        else:
            console.print("[red]Error:[/red] No pipeline configuration found")
            console.print("Create a pipeline.yml file or specify one with --config")
            raise typer.Exit(1)

    if dry_run:
        _show_dry_run(pipeline, global_config.agents)
        return

    # Execute pipeline
    executor = PipelineExecutor(working_dir=working_dir)
    executor.execute(pipeline, global_config.agents)


@app.command()
def init(
    name: Annotated[str, typer.Argument(help="Project name")] = "my-pipeline",
) -> None:
    """Initialize a new Relay project with example files."""
    # Create relay.yml
    config_content = f'''# Relay configuration
# Define your agents and pipelines here

agents:
  claude-code:
    command: claude
    args: ["--verbose"]

  opencode:
    command: opencode
    env:
      OPENCODE_MODEL: claude-3-5-sonnet

pipelines:
  default:
    - plan
    - code
    - review
'''

    # Create example pipeline
    pipeline_content = f'''name: "{name}"
description: "Example pipeline - customize for your needs"

steps:
  - name: plan
    agent: claude-code
    prompt: |
      Analyze the codebase and create a plan for the requested changes.
      Write your plan to plan.md.
    output: plan.md

  - name: code
    agent: opencode
    prompt: |
      Based on plan.md, implement the changes.
    input: plan.md
    output: implementation.md

  - name: review
    agent: claude-code
    prompt: |
      Review the implementation in implementation.md.
      Suggest improvements and identify any issues.
    input: implementation.md
    output: review.md
'''

    # Write files
    config_path = Path("relay.yml")
    pipeline_path = Path("pipeline.yml")

    if config_path.exists():
        console.print(f"[yellow]Warning:[/yellow] {config_path} already exists")
    else:
        config_path.write_text(config_content)
        console.print(f"[green]Created:[/green] {config_path}")

    if pipeline_path.exists():
        console.print(f"[yellow]Warning:[/yellow] {pipeline_path} already exists")
    else:
        pipeline_path.write_text(pipeline_content)
        console.print(f"[green]Created:[/green] {pipeline_path}")

    console.print(f"\n[bold]Next steps:[/bold]")
    console.print(f"  1. Edit {pipeline_path} to define your workflow")
    console.print(f"  2. Run: relay run")


@app.command()
def list_agents() -> None:
    """List configured agents."""
    config_path = find_config_file()
    config = load_config(config_path) if config_path else load_config(Path("/dev/null"))

    table = Table(title="Configured Agents")
    table.add_column("Name", style="cyan")
    table.add_column("Command", style="green")
    table.add_column("Args", style="dim")

    for name, agent in config.agents.items():
        table.add_row(name, agent.command, " ".join(agent.args))

    console.print(table)


@app.command()
def monitor(
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Pipeline to monitor (optional)"),
    ] = None,
    working_dir: Annotated[
        Path | None,
        typer.Option("--working-dir", "-w", help="Working directory"),
    ] = None,
) -> None:
    """Launch the terminal dashboard."""
    config_path = find_config_file()
    global_config = load_config(config_path) if config_path else load_config(Path("/dev/null"))

    if config:
        # Monitor a specific pipeline
        show_pipeline_status(config, global_config)
    else:
        # Show general dashboard
        run_dashboard(global_config, working_dir)


def _show_dry_run(pipeline: PipelineConfig, agents: dict) -> None:
    """Show what would be executed without running."""
    console.print(f"\n[bold]Pipeline:[/bold] {pipeline.name}")
    if pipeline.description:
        console.print(f"[dim]{pipeline.description}[/dim]")

    console.print(f"\n[bold]Steps ({len(pipeline.steps)}):[/bold]")
    for i, step in enumerate(pipeline.steps, 1):
        agent = agents.get(step.agent)
        cmd = f"{agent.command} {' '.join(agent.args)}" if agent else f"[{step.agent}]"
        console.print(f"  {i}. [cyan]{step.name}[/cyan] → {cmd}")
        if step.input:
            console.print(f"     Input: {step.input}")
        if step.output:
            console.print(f"     Output: {step.output}")


if __name__ == "__main__":
    app()
