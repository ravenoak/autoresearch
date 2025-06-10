"""
CLI entry point for Autoresearch with adaptive output formatting.
"""
import sys
import atexit
from typing import Optional

import typer

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
    typer.echo("Monitor mode not implemented yet.")

if __name__ == "__main__":
    app()

