from __future__ import annotations
from typing import Any

import typer


def ask(text: str, *args: Any, **kwargs: Any) -> str:
    """Prompt the user for input using Typer."""
    return typer.prompt(text, *args, **kwargs)
