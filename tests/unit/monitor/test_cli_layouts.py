"""Tests for CLI layout helpers with Rich and bare-mode fallbacks."""

from __future__ import annotations

import pytest
from rich.console import Group

from autoresearch.cli_utils import (
    get_console,
    render_metrics_panel,
    set_bare_mode,
    visualize_metrics_cli,
)


@pytest.fixture
def restore_console(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure bare mode and console state are reset after each test."""

    monkeypatch.delenv("AUTORESEARCH_BARE_MODE", raising=False)
    set_bare_mode(False)
    yield
    monkeypatch.delenv("AUTORESEARCH_BARE_MODE", raising=False)
    set_bare_mode(False)


def test_render_metrics_panel_rich_mode(restore_console: None) -> None:
    renderable = render_metrics_panel({"accuracy": 0.9, "latency": 12})
    assert isinstance(renderable, Group)


def test_visualize_metrics_cli_rich_output(restore_console: None) -> None:
    console = get_console(force_refresh=True)
    with console.capture() as capture:
        visualize_metrics_cli({"accuracy": 0.95, "latency": 120})
    output = capture.get()
    assert "accuracy" in output
    assert "╭" in output or "┌" in output


def test_visualize_metrics_cli_bare_mode(
    monkeypatch: pytest.MonkeyPatch, restore_console: None
) -> None:
    monkeypatch.setenv("AUTORESEARCH_BARE_MODE", "1")
    set_bare_mode(True)
    console = get_console(force_refresh=True)
    with console.capture() as capture:
        visualize_metrics_cli({"accuracy": 0.75, "latency": 80})
    output = capture.get()
    assert "Metrics:" in output
    assert "#" in output
    assert "╭" not in output and "┌" not in output
