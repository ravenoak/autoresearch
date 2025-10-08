"""CLI entry point for running Autoresearch via ``python -m``."""

from __future__ import annotations

from typing import Any, Callable, cast

from autoresearch.main import app

if __name__ == "__main__":
    run_cli = cast(Callable[..., Any], app)
    run_cli()
