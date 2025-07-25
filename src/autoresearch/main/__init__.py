"""CLI entry points."""

from .app import app, search, serve, serve_a2a
from .config_cli import config_app

__all__ = ["app", "search", "serve", "serve_a2a", "config_app"]
