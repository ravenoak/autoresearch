"""Tests for the Textual dashboard CLI integration."""

from __future__ import annotations

from typing import Any, Mapping

import pytest
from typer.testing import CliRunner

from autoresearch.config import ConfigModel
from autoresearch.main import app as cli_app
from autoresearch.main.app import _config_loader
from autoresearch.models import QueryResponse


class _DummyOrchestrator:
    """Stub orchestrator returning a static response for tests."""

    def run_query(
        self,
        query: str,
        config: ConfigModel,
        callbacks: Mapping[str, Any] | None = None,
        *,
        visualize: bool = False,
    ) -> QueryResponse:
        return QueryResponse(
            answer="done",
            citations=[],
            reasoning=[],
            metrics={},
        )


@pytest.fixture(autouse=True)
def _reset_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure config loader returns a default configuration."""

    monkeypatch.setattr(_config_loader, "load_config", lambda: ConfigModel())
    monkeypatch.setenv("AUTORESEARCH_BARE_MODE", "false")
    monkeypatch.setattr("autoresearch.main.app.StorageManager.setup", lambda: None)
    monkeypatch.setattr("autoresearch.main.app.StorageManager.load_ontology", lambda *_: None)
    monkeypatch.setattr("autoresearch.main.app.Orchestrator", _DummyOrchestrator)


def test_search_tui_fallback_when_not_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI should fall back to legacy rendering when stdout is not a TTY."""

    monkeypatch.setattr("autoresearch.main.app.sys.stdout.isatty", lambda: False)

    def _should_not_run(**_: Any) -> QueryResponse:
        raise AssertionError("dashboard should not run")

    monkeypatch.setattr("autoresearch.ui.tui.run_dashboard", _should_not_run)

    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "--tui", "test query"])

    assert result.exit_code == 0, result.stdout
    assert "Interactive dashboard requires a TTY" in result.stdout
    assert "Query processed successfully" in result.stdout


def test_search_tui_invokes_dashboard_when_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI should call the dashboard runner when a TTY is available."""

    monkeypatch.setattr("autoresearch.main.app.sys.stdout.isatty", lambda: True)

    captured: dict[str, Any] = {}

    def _fake_dashboard(*, runner: Any, total_loops: int, hooks: Any) -> QueryResponse:
        captured["total_loops"] = total_loops
        captured["hooks"] = hooks
        return QueryResponse(
            answer="ok",
            citations=[],
            reasoning=[],
            metrics={},
        )

    monkeypatch.setattr("autoresearch.ui.tui.run_dashboard", _fake_dashboard)

    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "--tui", "another query"])

    assert result.exit_code == 0, result.stdout
    assert captured.get("total_loops") == 1
    assert "Query processed successfully" in result.stdout
