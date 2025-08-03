"""Small helper utilities used by the CLI."""
from __future__ import annotations

import difflib
from typing import Sequence, List

import click
import typer

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
