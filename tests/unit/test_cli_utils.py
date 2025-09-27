"""Unit tests for CLI utility helpers."""

import typer

from autoresearch.cli_utils import attach_cli_hooks


def test_attach_cli_hooks_exposes_attributes() -> None:
    app = typer.Typer()

    def visualize() -> None:  # pragma: no cover - simple stub
        return None

    def visualize_query() -> None:  # pragma: no cover - simple stub
        return None

    attach_cli_hooks(app, visualize=visualize, visualize_query=visualize_query, name="demo")

    assert getattr(app, "name") == "demo"
    assert getattr(app, "_cli_visualize") is visualize
    assert getattr(app, "_cli_visualize_query") is visualize_query
