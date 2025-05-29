"""
CLI entry point for Autoresearch with adaptive output formatting.
"""
import sys
from typing import Optional
import typer

from .config import ConfigLoader
from .orchestration.orchestrator import Orchestrator
from .output_format import OutputFormatter

app = typer.Typer(help="Autoresearch CLI entry point")

@app.command()
def search(
    query: str = typer.Argument(..., help="Natural-language query to process"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output format: json|markdown|plain"),
):
    """Run a search query through the orchestrator and format the result."""
    config = ConfigLoader.load_config()
    result = Orchestrator.run_query(query, config)
    fmt = output or ("json" if not sys.stdout.isatty() else "markdown")
    OutputFormatter.format(result, fmt)

@app.command()
def config():
    """Display current configuration."""
    config = ConfigLoader.load_config()
    typer.echo(config.json(indent=2))

@app.command()
def monitor():
    """Start interactive resource and metrics monitor (TUI)."""
    typer.echo("Monitor mode not implemented yet.")

if __name__ == "__main__":
    app()

