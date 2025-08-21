"""CLI entry points and utilities exposed for testing.

This module re-exports objects from :mod:`app` and includes selected
dependencies so tests can monkeypatch them directly.  In particular the
integration test suite replaces :class:`rich.progress.Progress` and the
``Prompt`` helper to avoid interactive output.  Importing them here keeps
the test paths simple and ensures all spawned processes are properly
cleaned up after each test run.
"""

from rich.progress import Progress

from . import Prompt
from .app import app, search, serve, serve_a2a
from .config_cli import config_app

__all__ = [
    "app",
    "search",
    "serve",
    "serve_a2a",
    "config_app",
    "Progress",
    "Prompt",
]
