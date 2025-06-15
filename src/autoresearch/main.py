"""CLI entry point for Autoresearch with adaptive output formatting."""

from __future__ import annotations

import sys
import os
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from .config import ConfigLoader
from .orchestration.orchestrator import Orchestrator
from .orchestration.state import QueryState
from .output_format import OutputFormatter
from .logging_utils import configure_logging
from .storage import StorageManager

app = typer.Typer(
    help=(
        "Autoresearch CLI entry point.\n\n"
        "Set the reasoning mode in autoresearch.toml under "
        "[core.reasoning_mode]. Valid values: direct, dialectical, "
        "chain-of-thought."
    ),
    name="autoresearch",
)
configure_logging()
_config_loader: ConfigLoader = ConfigLoader()


@app.callback(invoke_without_command=False)
def start_watcher(ctx: typer.Context) -> None:
    """Start configuration watcher before executing commands."""
    StorageManager.setup()
    watch_ctx = _config_loader.watching()
    watch_ctx.__enter__()
    ctx.call_on_close(lambda: watch_ctx.__exit__(None, None, None))


@app.command()
def search(
    query: str = typer.Argument(..., help="Natural-language query to process"),
    output: Optional[str] = typer.Option(
        None, "-o", "--output", help="Output format: json|markdown|plain"
    ),
) -> None:
    """Run a search query through the orchestrator and format the result."""
    config = _config_loader.load_config()
    console = Console()

    try:
        result = Orchestrator.run_query(query, config)
        fmt = output or (
            "markdown"
            if os.getenv("PYTEST_CURRENT_TEST")
            else ("json" if not sys.stdout.isatty() else "markdown")
        )
        OutputFormatter.format(result, fmt)
    except Exception as e:
        # Create a valid QueryResponse object with error information
        from .models import QueryResponse
        error_result = QueryResponse(
            answer=f"Error: {str(e)}",
            citations=[],
            reasoning=["An error occurred during processing.", "Please check the logs for details."],
            metrics={"error": str(e)}
        )
        fmt = output or (
            "markdown"
            if os.getenv("PYTEST_CURRENT_TEST")
            else ("json" if not sys.stdout.isatty() else "markdown")
        )
        OutputFormatter.format(error_result, fmt)


@app.command()
def config() -> None:
    """Display current configuration."""
    config = _config_loader.load_config()
    typer.echo(config.json(indent=2))


@app.command()
def monitor() -> None:
    """Start interactive resource and metrics monitor (TUI)."""
    console = Console()
    config = _config_loader.load_config()

    abort_flag = {"stop": False}

    def on_cycle_end(loop: int, state: QueryState) -> None:
        metrics = state.metadata.get("execution_metrics", {})
        table = Table(title=f"Cycle {loop + 1} Metrics")
        table.add_column("Metric")
        table.add_column("Value")
        for k, v in metrics.items():
            table.add_row(str(k), str(v))
        console.print(table)
        feedback = Prompt.ask("Feedback (q to stop)", default="")
        if feedback.lower() == "q":
            state.error_count = getattr(config, "max_errors", 3)
            abort_flag["stop"] = True
        elif feedback:
            state.claims.append({"type": "feedback", "text": feedback})

    while True:
        query = Prompt.ask("Enter query (q to quit)")
        if not query or query.lower() == "q":
            break

        try:
            result = Orchestrator.run_query(
                query, config, {"on_cycle_end": on_cycle_end}
            )
            fmt = config.output_format or (
                "json" if not sys.stdout.isatty() else "markdown"
            )
            OutputFormatter.format(result, fmt)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            # Continue with the next query instead of exiting with error

        if abort_flag["stop"]:
            break


if __name__ == "__main__":
    app()
