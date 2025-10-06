from __future__ import annotations
from typing import Any

import typer


def ask(text: str, *args: Any, **kwargs: Any) -> str:
    """Prompt the user for input using Typer.

    Args:
        text: Prompt shown to the user.
        *args: Positional arguments forwarded to :func:`typer.prompt`.
        **kwargs: Keyword arguments forwarded to :func:`typer.prompt`.

    Returns:
        User input collected by Typer as a string.
    """

    return typer.prompt(text, *args, **kwargs)
