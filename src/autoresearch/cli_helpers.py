"""Small helper utilities used by the CLI."""
from __future__ import annotations

import difflib
from typing import Iterable, List, Mapping, Sequence, Tuple

import click
import typer

from rich.console import Console
from fastapi import HTTPException

from .cli_utils import (
    print_error,
    print_info,
    print_command_example,
)
from .output_format import DepthLevel


DEPTH_LEVEL_ORDER: Tuple[DepthLevel, ...] = (
    DepthLevel.TLDR,
    DepthLevel.KEY_FINDINGS,
    DepthLevel.CLAIMS,
    DepthLevel.TRACE,
)

DEPTH_FLAG_CHOICES: Tuple[str, ...] = tuple(level.value for level in DEPTH_LEVEL_ORDER) + (
    DepthLevel.FULL.value,
)

DEPTH_FLAG_HELP: str = (
    "Add detail layers to CLI output. Repeat --depth with values: tldr, findings, "
    "claims, trace, or full for every layer."
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


def parse_depth_flags(flags: Iterable[str] | None) -> List[DepthLevel]:
    """Normalize ``--depth`` flags into ``DepthLevel`` values."""

    if not flags:
        return []

    seen: set[DepthLevel] = set()
    for raw in flags:
        candidate = str(raw).lower()
        try:
            level = DepthLevel(candidate)
        except ValueError as exc:  # pragma: no cover - defensive branch
            valid = ", ".join(DEPTH_FLAG_CHOICES)
            raise typer.BadParameter(
                f"Unknown depth flag '{raw}'. Choose from: {valid}"
            ) from exc

        if level is DepthLevel.FULL:
            return list(DEPTH_LEVEL_ORDER)

        seen.add(level)

    ordered: List[DepthLevel] = []
    for level in DEPTH_LEVEL_ORDER:
        if level in seen:
            ordered.append(level)

    return ordered


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
