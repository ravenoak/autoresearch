"""CLI utilities for consistent formatting and accessibility.

This module provides utilities for consistent formatting of CLI output
with accessibility in mind. It includes functions for formatting messages
with both color and text-based alternatives, as well as symbolic indicators.
"""

import os
from enum import Enum
from typing import Optional
from rich.console import Console


# Verbosity levels
class Verbosity(str, Enum):
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
