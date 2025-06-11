"""
CLI entry point for Autoresearch with adaptive output formatting.
"""
import sys
import atexit
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from .config import ConfigLoader
from .orchestration.orchestrator import Orchestrator
from .output_format import OutputFormatter
from .logging_utils import configure_logging

app = typer.Typer(help="Autoresearch CLI entry point")
configure_logging()
_config_loader = ConfigLoader()

@app.callback(invoke_without_command=False)
def start_watcher(ctx: typer.Context):
    """Start configuration watcher before executing commands."""
    _config_loader.watch_changes()
    atexit.register(_config_loader.stop_watching)

@app.command()
def search(
    query: str = typer.Argument(..., help="Natural-language query to process"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output format: json|markdown|plain"),
):
    """Run a search query through the orchestrator and format the result."""
    config = _config_loader.load_config()
    result = Orchestrator.run_query(query, config)
    fmt = output or ("json" if not sys.stdout.isatty() else "markdown")
    OutputFormatter.format(result, fmt)

@app.command()
def config():
    """Display current configuration."""
    config = _config_loader.load_config()
    typer.echo(config.json(indent=2))

@app.command()
def monitor():
    """Start interactive resource and metrics monitor (TUI)."""
    console = Console()
    config = _config_loader.load_config()

    query = Prompt.ask("Enter query")
    abort_flag = {"stop": False}

    def on_cycle_end(loop: int, state):
        metrics = state.metadata.get("execution_metrics", {})
        table = Table(title=f"Cycle {loop + 1} Metrics")
        table.add_column("Metric")
        table.add_column("Value")
        for k, v in metrics.items():
            table.add_row(str(k), str(v))
        console.print(table)
        feedback = Prompt.ask("Feedback (q to quit)", default="")
        if feedback.lower() == "q":
            state.error_count = config.max_errors
            abort_flag["stop"] = True
        elif feedback:
            state.claims.append({"type": "feedback", "text": feedback})

    result = Orchestrator.run_query(query, config, {"on_cycle_end": on_cycle_end})
    fmt = config.output_format or ("json" if not sys.stdout.isatty() else "markdown")
    OutputFormatter.format(result, fmt)

if __name__ == "__main__":
    app()

