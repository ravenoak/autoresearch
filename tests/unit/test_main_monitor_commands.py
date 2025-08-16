from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from autoresearch.main import app


def test_monitor_command(monkeypatch):
    """Monitor command prints system metrics."""
    runner = CliRunner()
    monkeypatch.setattr(
        "autoresearch.monitor._collect_system_metrics", lambda: {"cpu_percent": 1.0}
    )
    result = runner.invoke(app, ["monitor"])
    assert result.exit_code == 0
    assert "cpu_percent" in result.stdout


@patch("autoresearch.a2a_interface.A2AInterface")
def test_serve_a2a_command(mock_a2a_interface_class):
    """Test the serve-a2a command."""
    # Setup
    runner = CliRunner()
    mock_a2a_interface = MagicMock()
    mock_a2a_interface.start.side_effect = SystemExit
    mock_a2a_interface_class.return_value = mock_a2a_interface

    result = runner.invoke(app, ["serve-a2a", "--host", "localhost", "--port", "8765"])

    assert result.exit_code == 0
    mock_a2a_interface_class.assert_called_once_with(host="localhost", port=8765)
    assert "Starting A2A server" in result.stdout


@patch("autoresearch.a2a_interface.A2AInterface")
def test_serve_a2a_command_keyboard_interrupt(mock_a2a_interface_class):
    """Test the serve-a2a command with KeyboardInterrupt."""
    # Setup
    runner = CliRunner()
    mock_a2a_interface = MagicMock()
    mock_a2a_interface.start.side_effect = KeyboardInterrupt
    mock_a2a_interface_class.return_value = mock_a2a_interface

    result = runner.invoke(app, ["serve-a2a"])

    assert result.exit_code == 0
    mock_a2a_interface_class.assert_called_once()
    assert "Starting A2A server" in result.stdout
    assert "Server stopped" in result.stdout
