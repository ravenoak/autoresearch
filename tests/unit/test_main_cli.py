from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from autoresearch.main import app
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator


def _mock_run_query(query, config):
    return QueryResponse(answer="a", citations=[], reasoning=[], metrics={})


def test_search_default_output_tty(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr(Orchestrator, "run_query", _mock_run_query)
    result = runner.invoke(app, ["search", "q"])
    assert result.exit_code == 0
    assert "# Answer" in result.stdout


def test_search_default_output_json(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    monkeypatch.setattr(Orchestrator, "run_query", _mock_run_query)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    result = runner.invoke(app, ["search", "q"])
    assert result.exit_code == 0
    assert result.stdout.strip().startswith("{")


def test_config_command(monkeypatch):
    runner = CliRunner()

    class Cfg:
        def json(self, indent=2):
            return '{\n  "loops": 1\n}'

    monkeypatch.setattr(
        "autoresearch.main._config_loader.load_config",
        lambda: Cfg(),
    )
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert '"loops"' in result.stdout


@patch("autoresearch.mcp_interface.create_server")
def test_serve_command(mock_create_server, monkeypatch):
    """Test the serve command that starts an MCP server."""
    runner = CliRunner()

    # Create mock objects
    mock_server_instance = MagicMock()
    mock_create_server.return_value = mock_server_instance

    # Mock the config loader
    class Cfg:
        def __init__(self):
            pass

    monkeypatch.setattr(
        "autoresearch.main._config_loader.load_config",
        lambda: Cfg(),
    )

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
