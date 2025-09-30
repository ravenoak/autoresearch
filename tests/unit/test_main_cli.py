from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from types import MethodType
import sys
import pytest
import importlib
from typing import Any


sys.modules.setdefault("bertopic", MagicMock())
sys.modules.setdefault("umap", MagicMock())
sys.modules.setdefault("pynndescent", MagicMock())

from autoresearch.models import QueryResponse  # noqa: E402


pytestmark = pytest.mark.usefixtures("dummy_storage")


def _main():
    return importlib.import_module("autoresearch.main")


def _app_mod():
    return importlib.import_module("autoresearch.main.app")


def test_search_default_output_tty(monkeypatch: pytest.MonkeyPatch, mock_run_query: Any, orchestrator: Any) -> None:
    runner = CliRunner()
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    orch = orchestrator
    monkeypatch.setattr(orch, "run_query", MethodType(mock_run_query, orch))
    monkeypatch.setattr(_app_mod(), "Orchestrator", lambda: orch)
    result = runner.invoke(_main().app, ["search", "q"])
    assert result.exit_code == 0
    assert "# Answer" in result.stdout


def test_search_default_output_json(monkeypatch: pytest.MonkeyPatch, mock_run_query: Any, orchestrator: Any) -> None:
    runner = CliRunner()
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    orch = orchestrator
    monkeypatch.setattr(orch, "run_query", MethodType(mock_run_query, orch))
    monkeypatch.setattr(_app_mod(), "Orchestrator", lambda: orch)
    result = runner.invoke(_main().app, ["search", "q"])
    assert result.exit_code == 0
    assert "{" in result.stdout


@pytest.mark.parametrize("mode", ["direct", "dialectical"])
def test_search_reasoning_mode_option(monkeypatch: pytest.MonkeyPatch, mode: Any, config_loader: Any, orchestrator: Any) -> None:
    runner = CliRunner()

    captured = {}

    def _run(
        self,
        query,
        config,
        callbacks=None,
        *,
        agent_factory=None,
        storage_manager=None,
        visualize=False,
    ):
        captured["mode"] = config.reasoning_mode
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(_app_mod(), "_config_loader", config_loader)
    orch = orchestrator
    monkeypatch.setattr(orch, "run_query", MethodType(_run, orch))
    monkeypatch.setattr(_app_mod(), "Orchestrator", lambda: orch)

    result = runner.invoke(_main().app, ["search", "q", "--reasoning-mode", mode])

    assert result.exit_code == 0
    assert captured["mode"].value == mode


def test_search_primus_start_option(monkeypatch: pytest.MonkeyPatch, config_loader: Any, orchestrator: Any) -> None:
    runner = CliRunner()

    captured = {}

    def _run(
        self,
        query,
        config,
        callbacks=None,
        *,
        agent_factory=None,
        storage_manager=None,
        visualize=False,
    ):
        captured["start"] = config.primus_start
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(_app_mod(), "_config_loader", config_loader)
    orch = orchestrator
    monkeypatch.setattr(orch, "run_query", MethodType(_run, orch))
    monkeypatch.setattr(_app_mod(), "Orchestrator", lambda: orch)

    result = runner.invoke(_main().app, ["search", "q", "--primus-start", "2"])

    assert result.exit_code == 0
    assert captured["start"] == 2


def test_config_command(monkeypatch: pytest.MonkeyPatch, config_loader: Any) -> None:
    runner = CliRunner()
    from autoresearch.config.models import ConfigModel

    monkeypatch.setattr(ConfigModel, "json", ConfigModel.model_dump_json)
    monkeypatch.setattr(_app_mod(), "_config_loader", config_loader)
    result = runner.invoke(_main().app, ["config"])
    assert result.exit_code == 0
    assert '"loops"' in result.stdout


@patch("autoresearch.main.app.create_server")
def test_serve_command(mock_create_server: Any, monkeypatch: pytest.MonkeyPatch, config_loader: Any) -> None:
    """Test the serve command that starts an MCP server."""
    runner = CliRunner()

    # Create mock objects
    mock_server_instance = MagicMock()
    mock_create_server.return_value = mock_server_instance

    # Mock the config loader
    monkeypatch.setattr(_app_mod(), "_config_loader", config_loader)

    # Run the command with Ctrl+C simulation
    mock_server_instance.run.side_effect = KeyboardInterrupt()
    result = runner.invoke(
        _main().app, ["serve", "--host", "localhost", "--port", "8888"]
    )

    # Verify the command executed successfully
    assert result.exit_code == 0

    # Verify the server was created with the correct parameters
    mock_create_server.assert_called_once_with(host="localhost", port=8888)

    # Verify the server was started
    mock_server_instance.run.assert_called_once()

    # Verify that a tool was registered (tool is a decorator)
    assert hasattr(mock_server_instance, "tool")
