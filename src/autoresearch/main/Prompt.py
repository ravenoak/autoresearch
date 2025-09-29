from __future__ import annotations
from typing import Any, cast

import typer


def ask(text: str, *args: Any, **kwargs: Any) -> str:
    """Prompt the user for input using Typer."""
    return cast(str, typer.prompt(text, *args, **kwargs))
