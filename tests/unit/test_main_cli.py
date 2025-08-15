from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
import sys
import pytest


sys.modules.setdefault("bertopic", MagicMock())
sys.modules.setdefault("umap", MagicMock())
sys.modules.setdefault("pynndescent", MagicMock())

from autoresearch.main import app  # noqa: E402
import importlib  # noqa: E402
main_app = importlib.import_module("autoresearch.main.app")  # noqa: E402
from autoresearch.models import QueryResponse  # noqa: E402
from autoresearch.orchestration.orchestrator import Orchestrator  # noqa: E402


def test_search_default_output_tty(monkeypatch, mock_run_query):
    runner = CliRunner()
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr(Orchestrator, "run_query", mock_run_query)
    result = runner.invoke(app, ["search", "q"])
    assert result.exit_code == 0
    assert "# Answer" in result.stdout


def test_search_default_output_json(monkeypatch, mock_run_query):
    runner = CliRunner()
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    monkeypatch.setattr(Orchestrator, "run_query", mock_run_query)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    result = runner.invoke(app, ["search", "q"])
    assert result.exit_code == 0
    assert "{" in result.stdout


@pytest.mark.parametrize("mode", ["direct", "dialectical"])
def test_search_reasoning_mode_option(monkeypatch, mode, config_loader):
    runner = CliRunner()

    captured = {}

    def _run(self, query, config, callbacks=None):
        captured["mode"] = config.reasoning_mode
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(main_app, "_config_loader", config_loader)
    monkeypatch.setattr(Orchestrator, "run_query", _run)

    result = runner.invoke(app, ["search", "q", "--reasoning-mode", mode])

    assert result.exit_code == 0
    assert captured["mode"].value == mode


def test_search_primus_start_option(monkeypatch, config_loader):
    runner = CliRunner()

    captured = {}

    def _run(self, query, config, callbacks=None):
        captured["start"] = config.primus_start
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(main_app, "_config_loader", config_loader)
    monkeypatch.setattr(Orchestrator, "run_query", _run)

    result = runner.invoke(app, ["search", "q", "--primus-start", "2"])

    assert result.exit_code == 0
    assert captured["start"] == 2


def test_config_command(monkeypatch, config_loader):
    runner = CliRunner()
    from autoresearch.config.models import ConfigModel

    monkeypatch.setattr(ConfigModel, "json", ConfigModel.model_dump_json)
    monkeypatch.setattr(main_app, "_config_loader", config_loader)
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert '"loops"' in result.stdout


@patch("autoresearch.main.app.create_server")
def test_serve_command(mock_create_server, monkeypatch, config_loader):
    """Test the serve command that starts an MCP server."""
    runner = CliRunner()

    # Create mock objects
    mock_server_instance = MagicMock()
    mock_create_server.return_value = mock_server_instance

    # Mock the config loader
    monkeypatch.setattr(main_app, "_config_loader", config_loader)

    # Run the command with Ctrl+C simulation
    mock_server_instance.run.side_effect = KeyboardInterrupt()
    result = runner.invoke(app, ["serve", "--host", "localhost", "--port", "8888"])

    # Verify the command executed successfully
    assert result.exit_code == 0

    # Verify the server was created with the correct parameters
    mock_create_server.assert_called_once_with(host="localhost", port=8888)

    # Verify the server was started
    mock_server_instance.run.assert_called_once()

    # Verify that a tool was registered (tool is a decorator)
    assert hasattr(mock_server_instance, "tool")
