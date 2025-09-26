"""Small helper utilities used by the CLI."""
from __future__ import annotations

import difflib
from typing import Sequence, List, Mapping, Optional

import click
import typer

from rich.console import Console
from fastapi import HTTPException

from .output_format import (
    OutputDepth,
    describe_depth_features,
    describe_depth_levels,
    get_depth_aliases,
    normalize_depth,
)

from .cli_utils import (
    print_error,
    print_info,
    print_command_example,
)


def find_similar_commands(
    command: str, valid_commands: Sequence[str], threshold: float = 0.6
) -> List[str]:
    """Return a list of commands similar to ``command``."""
    matches = difflib.get_close_matches(command, valid_commands, n=3, cutoff=threshold)
    return list(matches)


def parse_agent_groups(groups: Sequence[str]) -> List[List[str]]:
    """Parse ``--agent-groups`` values into structured lists.

    Each entry in ``groups`` is expected to be a comma-separated string of
    agent names. Whitespace around agent names is ignored and empty names are
    discarded. The return value is a list of agent groups where each group is
    represented as a list of agent names.
    """
    parsed: List[List[str]] = []
    for grp in groups:
        agents = [a.strip() for a in grp.split(",") if a.strip()]
        if agents:
            parsed.append(agents)
    return parsed


def require_api_key(headers: Mapping[str, str]) -> None:
    """Ensure an ``X-API-Key`` header is present.

    Args:
        headers: Mapping of request headers.

    Raises:
        HTTPException: ``401`` when the header is missing.
    """

    if "X-API-Key" not in headers:
        raise HTTPException(
            status_code=401,
            detail="Missing API key",
            headers={"WWW-Authenticate": "API-Key"},
        )


def report_missing_tables(tables: Sequence[str], console: Console | None = None) -> None:
    """Report missing database tables in a user-friendly way."""
    if not tables:
        return
    names = ", ".join(sorted(tables))
    if console is None:
        print_error(
            f"Missing required tables: {names}",
            suggestion="Ensure the storage schema has been initialized.",
        )
    else:
        console.print(f"[bold red]Missing required tables: {names}[/bold red]")
        console.print(
            "[yellow]Suggestion:[/yellow] "
            "Ensure the storage schema has been initialized."
        )


def handle_command_not_found(ctx: typer.Context, command: str) -> None:
    """Display a friendly error message when a command is not found."""
    print_error(f"Command '{command}' not found.")

    available_commands: List[str] = []
    if isinstance(ctx.command, click.Group):
        for command_obj in ctx.command.commands.values():
            if command_obj.name:
                available_commands.append(command_obj.name)

    similar_commands = find_similar_commands(command, available_commands)
    if similar_commands:
        print_info("Did you mean:", symbol=False)
    for name in similar_commands:
        print_command_example(name)

    typer.secho("\nRun 'autoresearch --help' to see all available commands.")
    raise typer.Exit(code=1)


def depth_option_callback(value: Optional[str]) -> Optional[OutputDepth]:
    """Parse ``--depth`` option values into :class:`OutputDepth`."""

    if value is None:
        return None
    try:
        return normalize_depth(value)
    except ValueError as exc:  # pragma: no cover - typer handles user feedback
        raise typer.BadParameter(str(exc)) from exc


def depth_help_text() -> str:
    """Return a human-readable description of depth choices."""

    descriptions = describe_depth_levels()
    features = describe_depth_features()
    feature_labels = {
        "tldr": "TL;DR",
        "key_findings": "key findings",
        "claim_audits": "claim table",
        "full_trace": "full trace",
    }
    parts: List[str] = []
    for depth in OutputDepth:
        desc = descriptions[depth]
        enabled = [
            label
            for key, label in feature_labels.items()
            if features.get(depth, {}).get(key, False)
        ]
        if enabled:
            desc = f"{desc} (includes {', '.join(enabled)})"
        else:
            desc = f"{desc} (answer only)"
        parts.append(f"{depth.label.lower()}: {desc}")
    aliases = sorted({k for k in get_depth_aliases().keys() if k.isalpha()})
    return (
        " | ".join(parts)
        + f". Aliases: {', '.join(aliases)} or 0-3."
    )
