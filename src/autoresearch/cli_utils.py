"""CLI utilities for consistent formatting and accessibility.

This module provides utilities for consistent formatting of CLI output
with accessibility in mind. It includes functions for formatting messages
with both color and text-based alternatives, as well as symbolic indicators.
"""

import os
import sys
from enum import Enum
from typing import Any, Optional
from rich.console import Console


# Verbosity levels
class Verbosity(str, Enum):
    """Verbosity levels supported by the CLI output helpers."""

    QUIET = "quiet"
    NORMAL = "normal"
    VERBOSE = "verbose"


# Global verbosity setting (default: NORMAL)
VERBOSITY = Verbosity.NORMAL

# Global console instance
console = Console()


def set_verbosity(level: Verbosity) -> None:
    """Set the global verbosity level.

    Args:
        level: The verbosity level to set
    """
    global VERBOSITY
    VERBOSITY = level

    # Set environment variable for other components
    os.environ["AUTORESEARCH_VERBOSITY"] = level.value


def get_verbosity() -> Verbosity:
    """Get the current verbosity level.

    Returns:
        The current verbosity level
    """
    return VERBOSITY


def format_success(message: str, symbol: bool = True) -> str:
    """Format a success message with color and optional symbol.

    Args:
        message: The message to format
        symbol: Whether to include a symbol

    Returns:
        The formatted message
    """
    if symbol:
        return f"[bold green]✓[/bold green] {message}"
    return f"[bold green]{message}[/bold green]"


def format_error(message: str, symbol: bool = True) -> str:
    """Format an error message with color and optional symbol.

    Args:
        message: The message to format
        symbol: Whether to include a symbol

    Returns:
        The formatted message
    """
    if symbol:
        return f"[bold red]✗[/bold red] {message}"
    return f"[bold red]Error:[/bold red] {message}"


def format_warning(message: str, symbol: bool = True) -> str:
    """Format a warning message with color and optional symbol.

    Args:
        message: The message to format
        symbol: Whether to include a symbol

    Returns:
        The formatted message
    """
    if symbol:
        return f"[bold yellow]⚠[/bold yellow] {message}"
    return f"[bold yellow]Warning:[/bold yellow] {message}"


def format_info(message: str, symbol: bool = True) -> str:
    """Format an info message with color and optional symbol.

    Args:
        message: The message to format
        symbol: Whether to include a symbol

    Returns:
        The formatted message
    """
    if symbol:
        return f"[bold blue]ℹ[/bold blue] {message}"
    return f"[bold blue]Info:[/bold blue] {message}"


def print_success(
    message: str, symbol: bool = True, min_verbosity: Verbosity = Verbosity.NORMAL
) -> None:
    """Print a success message with color and optional symbol.

    Args:
        message: The message to print
        symbol: Whether to include a symbol
        min_verbosity: Minimum verbosity level required to print this message
    """
    if VERBOSITY.value >= min_verbosity.value:
        console.print(format_success(message, symbol))


def print_error(
    message: str,
    symbol: bool = True,
    min_verbosity: Verbosity = Verbosity.QUIET,
    suggestion: Optional[str] = None,
    code_example: Optional[str] = None,
) -> None:
    """Print an error message with color, optional symbol, and actionable suggestions.

    Args:
        message: The message to print
        symbol: Whether to include a symbol
        min_verbosity: Minimum verbosity level required to print this message
        suggestion: Optional suggestion for resolving the error
        code_example: Optional code example for resolving the error
    """
    if VERBOSITY.value >= min_verbosity.value:
        console.print(format_error(message, symbol))

        # Print suggestion if provided
        if suggestion:
            console.print(f"[yellow]Suggestion:[/yellow] {suggestion}")

        # Print code example if provided
        if code_example:
            console.print(f"[yellow]Example:[/yellow] [cyan]{code_example}[/cyan]")


def print_warning(
    message: str, symbol: bool = True, min_verbosity: Verbosity = Verbosity.NORMAL
) -> None:
    """Print a warning message with color and optional symbol.

    Args:
        message: The message to print
        symbol: Whether to include a symbol
        min_verbosity: Minimum verbosity level required to print this message
    """
    if VERBOSITY.value >= min_verbosity.value:
        console.print(format_warning(message, symbol))


def print_info(
    message: str, symbol: bool = True, min_verbosity: Verbosity = Verbosity.NORMAL
) -> None:
    """Print an info message with color and optional symbol.

    Args:
        message: The message to print
        symbol: Whether to include a symbol
        min_verbosity: Minimum verbosity level required to print this message
    """
    if VERBOSITY.value >= min_verbosity.value:
        console.print(format_info(message, symbol))


def print_verbose(message: str, symbol: bool = True) -> None:
    """Print a verbose message with color and optional symbol.

    Args:
        message: The message to print
        symbol: Whether to include a symbol
    """
    if VERBOSITY == Verbosity.VERBOSE:
        console.print(format_info(message, symbol))


def print_command_example(
    command: str,
    description: Optional[str] = None,
    min_verbosity: Verbosity = Verbosity.NORMAL,
) -> None:
    """Print a command example with optional description.

    Args:
        command: The command to print
        description: Optional description of the command
        min_verbosity: Minimum verbosity level required to print this message
    """
    if VERBOSITY.value >= min_verbosity.value:
        if description:
            console.print(f"[cyan]{command}[/cyan] - {description}")
        else:
            console.print(f"[cyan]{command}[/cyan]")


def visualize_rdf_cli(output_path: str) -> None:
    """Visualize the RDF graph and report the output path."""
    from .storage import StorageManager

    try:  # pragma: no cover - optional dependency
        StorageManager.visualize_rdf(output_path)
        print_success(f"Graph written to {output_path}")
    except Exception as e:  # pragma: no cover - optional dependency
        print_error(
            f"Failed to visualize RDF graph: {e}",
            suggestion="Ensure matplotlib is installed",
        )


def sparql_query_cli(query: str) -> None:
    """Run a SPARQL query with reasoning and display the results."""
    from .storage import StorageManager
    from tabulate import tabulate

    res = StorageManager.query_with_reasoning(query)
    if hasattr(res, "askAnswer"):
        print_info(f"ASK result: {res.askAnswer}")
        return

    rows = [list(r) for r in res]
    headers = [str(v) for v in res.vars]
    console.print(tabulate(rows, headers=headers, tablefmt="github"))


def visualize_query_cli(query: str, output_path: str) -> None:
    """Run a query and save a knowledge graph visualization."""
    from rich.progress import Progress

    from .config import ConfigLoader
    from .orchestration.orchestrator import Orchestrator
    from .monitor import _collect_system_metrics, _render_metrics
    from .output_format import OutputFormatter
    from .visualization import save_knowledge_graph

    loader = ConfigLoader()
    config = loader.load_config()
    loops = getattr(config, "loops", 1)

    with Progress() as progress:
        task = progress.add_task("[green]Processing query...", total=loops)

        def on_cycle_end(loop: int, _state: Any) -> None:
            progress.update(task, advance=1)

        result = Orchestrator.run_query(query, config, {"on_cycle_end": on_cycle_end})

    fmt = "json" if not sys.stdout.isatty() else "markdown"
    OutputFormatter.format(result, fmt)

    try:
        save_knowledge_graph(result, output_path)
        print_success(f"Graph written to {output_path}")
    except Exception as e:  # pragma: no cover - optional dependency
        print_error(
            f"Failed to create visualization: {e}",
            suggestion="Ensure matplotlib is installed",
        )

    metrics = {**result.metrics, **_collect_system_metrics()}
    console.print(_render_metrics(metrics))
