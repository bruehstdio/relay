"""Terminal dashboard for monitoring Relay pipelines."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from relay.models import RelayConfig

console = Console()


def make_layout() -> Layout:
    """Create the dashboard layout."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3),
    )
    layout["main"].split_row(
        Layout(name="sidebar", ratio=1),
        Layout(name="body", ratio=2),
    )
    layout["sidebar"].split_column(
        Layout(name="agents"),
        Layout(name="artifacts"),
    )
    return layout


def make_header(config: RelayConfig) -> Panel:
    """Create the header panel."""
    grid = Table.grid(expand=True)
    grid.add_column(justify="left", ratio=1)
    grid.add_column(justify="right")
    grid.add_row(
        "[bold blue]Relay Dashboard[/bold blue]",
        f"[dim]{len(config.agents)} agents configured[/dim]",
    )
    return Panel(grid, style="blue")


def make_agents_panel(config: RelayConfig) -> Panel:
    """Create the agents panel."""
    table = Table(show_header=False, box=None, expand=True)
    table.add_column("Agent", style="cyan")
    table.add_column("Command", style="green")

    for name, agent in sorted(config.agents.items()):
        cmd = f"{agent.command} {' '.join(agent.args)}".strip()
        if len(cmd) > 25:
            cmd = cmd[:22] + "..."
        table.add_row(name, cmd)

    return Panel(table, title="[bold]Agents[/bold]", border_style="cyan")


def make_artifacts_panel(artifacts_dir: Path) -> Panel:
    """Create the artifacts panel."""
    table = Table(show_header=False, box=None, expand=True)
    table.add_column("File", style="yellow")
    table.add_column("Size", justify="right", style="dim")

    if artifacts_dir.exists():
        files = sorted(artifacts_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        for f in files[:10]:  # Show last 10
            size = f.stat().st_size
            size_str = f"{size}B" if size < 1024 else f"{size//1024}KB"
            table.add_row(f.name, size_str)

    return Panel(table, title="[bold]Recent Artifacts[/bold]", border_style="yellow")


def make_body_panel() -> Panel:
    """Create the main body panel with pipeline status."""
    content = Text()
    content.append("Welcome to Relay Dashboard\n\n", style="bold")
    content.append("Quick Start:\n", style="cyan")
    content.append("  • relay init          Create a new pipeline\n")
    content.append("  • relay run           Execute a pipeline\n")
    content.append("  • relay list-agents   Show configured agents\n\n")
    content.append("Press ", style="dim")
    content.append("q", style="bold red")
    content.append(" to quit", style="dim")

    return Panel(content, title="[bold]Status[/bold]", border_style="green")


def make_footer() -> Panel:
    """Create the footer panel."""
    return Panel(
        "[dim]Relay v0.1.0 | https://github.com/danielfbmbot/relay[/dim]",
        style="dim",
    )


def run_dashboard(config: RelayConfig, working_dir: Path | None = None) -> None:
    """Run the terminal dashboard."""
    working_dir = working_dir or Path.cwd()
    artifacts_dir = working_dir / ".relay" / "artifacts"

    layout = make_layout()

    with Live(layout, refresh_per_second=4, screen=True):
        while True:
            # Update layout
            layout["header"].update(make_header(config))
            layout["agents"].update(make_agents_panel(config))
            layout["artifacts"].update(make_artifacts_panel(artifacts_dir))
            layout["body"].update(make_body_panel())
            layout["footer"].update(make_footer())

            time.sleep(0.25)


def show_pipeline_status(pipeline_file: Path, config: RelayConfig) -> None:
    """Show live status of a running pipeline."""
    from relay.config import load_pipeline
    from relay.executor import PipelineExecutor

    pipeline = load_pipeline(pipeline_file)

    # Create progress display
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )

    task = progress.add_task(f"[cyan]Pipeline: {pipeline.name}[/cyan]", total=len(pipeline.steps))

    with Live(progress, console=console, refresh_per_second=4):
        executor = PipelineExecutor()

        for i, step in enumerate(pipeline.steps, 1):
            progress.update(
                task, description=f"[cyan]Step {i}/{len(pipeline.steps)}: {step.name}[/cyan]"
            )

            # Execute single step
            result = executor._execute_step(i, step, config.agents, None)
            executor.results.append(result)

            if result.success:
                progress.console.print(f"[green]✓[/green] {step.name} ({result.duration_ms}ms)")
            else:
                progress.console.print(f"[red]✗[/red] {step.name}: {result.error}")
                if not step.continue_on_error:
                    break

            progress.advance(task)

        # Summary
        successful = sum(1 for r in executor.results if r.success)
        total = len(executor.results)
        color = "green" if successful == total else "yellow" if successful > 0 else "red"
        progress.console.print(
            f"\n[{color}]Pipeline complete: {successful}/{total} steps succeeded[/]"
        )
