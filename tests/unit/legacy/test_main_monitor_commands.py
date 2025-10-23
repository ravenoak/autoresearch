# mypy: ignore-errors
from unittest.mock import MagicMock, patch
import importlib
import pytest
from typer.testing import CliRunner  # Typer's CLI test runner


pytestmark = pytest.mark.usefixtures("dummy_storage")


def _main():
    return importlib.import_module("autoresearch.main")


def test_monitor_command(monkeypatch):
    """Monitor command help is accessible."""
    runner = CliRunner()
    result = runner.invoke(_main().app, ["monitor", "metrics", "--help"])
    assert result.exit_code == 0
    assert "metrics" in result.stdout


def test_serve_a2a_command(monkeypatch):
    """Test that serve-a2a command help is accessible."""
    runner = CliRunner()
    result = runner.invoke(_main().app, ["serve-a2a", "--help"])
    assert result.exit_code == 0
    assert "serve-a2a" in result.stdout


def test_monitor_serve_command(monkeypatch):
    """Test that monitor serve command help is accessible."""
    runner = CliRunner()
    result = runner.invoke(_main().app, ["monitor", "serve", "--help"])
    assert result.exit_code == 0
    assert "serve" in result.stdout


@patch("autoresearch.monitor.cli.NodeHealthMonitor")
def test_monitor_serve_command_keyboard_interrupt(mock_monitor_class):
    """Test the monitor serve command with KeyboardInterrupt."""
    runner = CliRunner()
    mock_monitor = MagicMock()
    mock_monitor.start.side_effect = KeyboardInterrupt
    mock_monitor_class.return_value = mock_monitor

    result = runner.invoke(_main().app, ["monitor", "serve"])

    assert result.exit_code == 0
    mock_monitor_class.assert_called_once()
    mock_monitor.start.assert_called_once()
    mock_monitor.stop.assert_called_once()
    assert "Server stopped" in result.stdout
