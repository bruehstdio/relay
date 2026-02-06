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
from relay.models import AgentConfig, PipelineConfig
from relay.templates import get_template_manager

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
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = OutputFormat.CONSOLE,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output file path"),
    ] = None,
    log_level: Annotated[
        LogLevel,
        typer.Option("--log-level", "-l", help="Log level"),
    ] = LogLevel.INFO,
    log_format: Annotated[
        str,
        typer.Option("--log-format", help="Log format (console or json)"),
    ] = "console",
) -> None:
    """Run a pipeline."""
    # Setup logging
    setup_logging(
        level=log_level,
        json_format=log_format.lower() == "json",
    )

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
    results = executor.execute(pipeline, global_config.agents)

    # Exit with error code if any step failed
    if any(not r.success for r in results):
        raise typer.Exit(1)


@app.command()
def init(
    name: Annotated[str, typer.Argument(help="Project name")] = "my-pipeline",
    template: Annotated[
        str | None,
        typer.Option("--template", "-t", help="Template to use (e.g., python-project)"),
    ] = None,
) -> None:
    """Initialize a new Relay project with example files."""
    # Create relay.yml
    config_content = '''# Relay configuration
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

    # Write relay.yml
    config_path = Path("relay.yml")
    if config_path.exists():
        console.print(f"[yellow]Warning:[/yellow] {config_path} already exists")
    else:
        config_path.write_text(config_content)
        console.print(f"[green]Created:[/green] {config_path}")

    # Create pipeline from template or default
    pipeline_path = Path("pipeline.yml")
    if pipeline_path.exists():
        console.print(f"[yellow]Warning:[/yellow] {pipeline_path} already exists")
    else:
        if template:
            # Use template
            manager = get_template_manager()
            try:
                template_data = manager.load_template(template)
                # Override name from template
                template_data["name"] = name
                # Remove description if it's the template's default
                if template_data.get("description", "").startswith("Template:"):
                    template_data.pop("description", None)

                import yaml
                pipeline_content = yaml.dump(
                    template_data, default_flow_style=False, sort_keys=False
                )
                pipeline_path.write_text(pipeline_content)
                console.print(
                    f"[green]Created:[/green] {pipeline_path} (from template: {template})"
                )
            except Exception as e:
                console.print(f"[red]Error loading template:[/red] {e}")
                raise typer.Exit(1)
        else:
            # Create default example pipeline
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
            pipeline_path.write_text(pipeline_content)
            console.print(f"[green]Created:[/green] {pipeline_path}")

    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  1. Edit {pipeline_path} to define your workflow")
    console.print("  2. Run: relay run")


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


def _show_dry_run(pipeline: PipelineConfig, agents: dict[str, AgentConfig]) -> None:
    """Show what would be executed without running."""
    console.print(f"\n[bold]Pipeline:[/bold] {pipeline.name}")
    if pipeline.description:
        console.print(f"[dim]{pipeline.description}[/dim]")

    console.print(f"\n[bold]Steps ({len(pipeline.steps)}):[/bold]")
    for i, step in enumerate(pipeline.steps, 1):
        agent = agents.get(step.agent) if step.agent else None
        cmd = f"{agent.command} {' '.join(agent.args)}" if agent else f"[{step.agent}]"
        console.print(f"  {i}. [cyan]{step.name}[/cyan] → {cmd}")
        if step.input:
            console.print(f"     Input: {step.input}")
        if step.output:
            console.print(f"     Output: {step.output}")


@app.command()
def visualize(
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Pipeline configuration file"),
    ] = None,
) -> None:
    """Visualize pipeline dependencies as a DAG."""
    console.print("[yellow]Visualization not yet implemented[/yellow]")
    raise typer.Exit(1)


# Template commands
template_app = typer.Typer(help="Manage pipeline templates")
app.add_typer(template_app, name="template")


@template_app.command("list")
def template_list() -> None:
    """List available templates."""
    manager = get_template_manager()
    templates = manager.list_templates()

    if not templates:
        console.print("[yellow]No templates found.[/yellow]")
        return

    table = Table(title="Available Templates")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="yellow")
    table.add_column("Source", style="green")
    table.add_column("Description", style="dim")

    for tmpl in templates:
        source_color = "blue" if tmpl["source"] == "builtin" else "magenta"
        table.add_row(
            tmpl["name"],
            tmpl["version"],
            f"[{source_color}]{tmpl['source']}[/{source_color}]",
            (
                tmpl["description"][:50] + "..."
                if len(tmpl["description"]) > 50
                else tmpl["description"]
            ),
        )

    console.print(table)


@template_app.command("show")
def template_show(
    name: Annotated[
        str,
        typer.Argument(
            help="Template name with optional version (e.g., python-project@1.0.0)"
        ),
    ],
) -> None:
    """Show template details."""
    manager = get_template_manager()

    try:
        info = manager.show_template(name)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]{info['name']}[/bold cyan] @ [yellow]{info['version']}[/yellow]")
    console.print(f"[dim]Source: {info['source']}[/dim]")
    console.print(f"\n{info['description']}")

    console.print("\n[bold]Steps:[/bold]")
    for step in info["data"].get("steps", []):
        console.print(f"  • [cyan]{step['name']}[/cyan] - {step.get('agent', 'N/A')}")


@template_app.command("install")
def template_install() -> None:
    """Install built-in templates to user directory (~/.relay/templates/)."""
    manager = get_template_manager()
    installed = manager.install_builtin_templates()

    if installed:
        console.print("[green]Installed templates:[/green]")
        for name in installed:
            console.print(f"  • {name}")
    else:
        console.print("[dim]All built-in templates are already installed.[/dim]")


# Cache commands
cache_app = typer.Typer(help="Manage artifact cache")
app.add_typer(cache_app, name="cache")


@cache_app.command("list")
def cache_list(
    working_dir: Annotated[
        Path | None,
        typer.Option("--working-dir", "-w", help="Working directory"),
    ] = None,
) -> None:
    """List cached artifacts."""
    from relay.cache import CacheManager
    from relay.config import find_config_file, load_config

    # Load config for cache settings
    config_path = find_config_file()
    config = load_config(config_path) if config_path else load_config(Path("/dev/null"))

    cache_manager = CacheManager.from_config(
        config.cache, working_dir=working_dir or Path.cwd()
    )
    entries = cache_manager.list_entries()

    if not entries:
        console.print("[dim]No cached artifacts found.[/dim]")
        return

    table = Table(title="Cached Artifacts")
    table.add_column("Key", style="cyan")
    table.add_column("Size", style="green")
    table.add_column("Created", style="yellow")

    import datetime

    for entry in entries:
        size_str = _format_size(entry.size)
        created_str = datetime.datetime.fromtimestamp(entry.created_at).strftime(
            "%Y-%m-%d %H:%M"
        )
        table.add_row(entry.key[:50], size_str, created_str)

    console.print(table)


@cache_app.command("clear")
def cache_clear(
    working_dir: Annotated[
        Path | None,
        typer.Option("--working-dir", "-w", help="Working directory"),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation"),
    ] = False,
) -> None:
    """Clear all cached artifacts."""
    from relay.cache import CacheManager
    from relay.config import find_config_file, load_config

    # Load config for cache settings
    config_path = find_config_file()
    config = load_config(config_path) if config_path else load_config(Path("/dev/null"))

    cache_manager = CacheManager.from_config(
        config.cache, working_dir=working_dir or Path.cwd()
    )
    entries = cache_manager.list_entries()

    if not entries:
        console.print("[dim]No cached artifacts to clear.[/dim]")
        return

    if not yes:
        confirm = typer.confirm(f"Clear {len(entries)} cache entries?")
        if not confirm:
            console.print("[dim]Cancelled.[/dim]")
            return

    count = cache_manager.clear()
    console.print(f"[green]Cleared {count} cache entries.[/green]")


def _format_size(size_bytes: float) -> str:
    """Format size in human-readable format."""
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


if __name__ == "__main__":
    app()
