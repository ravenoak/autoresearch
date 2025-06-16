import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from autoresearch.main import app


@patch("autoresearch.main.Console")
@patch("autoresearch.main.Orchestrator")
def test_monitor_command(mock_orchestrator_class, mock_console_class):
    """Test the monitor command."""
    # Setup
    runner = CliRunner()
    mock_orchestrator = MagicMock()
    mock_orchestrator_class.return_value = mock_orchestrator
    
    # Mock the on_cycle_end callback to be called once then raise KeyboardInterrupt
    def side_effect(callback):
        callback(1, MagicMock())
        raise KeyboardInterrupt()
    
    mock_orchestrator.set_cycle_end_callback.side_effect = side_effect
    
    # Execute
    result = runner.invoke(app, ["monitor"])
    
    # Verify
    assert result.exit_code == 0
    mock_orchestrator_class.assert_called_once()
    mock_orchestrator.set_cycle_end_callback.assert_called_once()
    assert "Starting monitor" in result.stdout
    assert "Monitor stopped" in result.stdout


@patch("autoresearch.main.asyncio")
@patch("autoresearch.main.A2AInterface")
def test_serve_a2a_command(mock_a2a_interface_class, mock_asyncio):
    """Test the serve-a2a command."""
    # Setup
    runner = CliRunner()
    mock_a2a_interface = MagicMock()
    mock_a2a_interface_class.return_value = mock_a2a_interface
    
    # Mock asyncio.run to return immediately
    mock_asyncio.run.return_value = None
    
    # Execute
    result = runner.invoke(app, ["serve-a2a", "--host", "localhost", "--port", "8765"])
    
    # Verify
    assert result.exit_code == 0
    mock_a2a_interface_class.assert_called_once_with(host="localhost", port=8765)
    mock_asyncio.run.assert_called_once_with(mock_a2a_interface.start_server())
    assert "Starting A2A server" in result.stdout


@patch("autoresearch.main.asyncio")
@patch("autoresearch.main.A2AInterface")
def test_serve_a2a_command_keyboard_interrupt(mock_a2a_interface_class, mock_asyncio):
    """Test the serve-a2a command with KeyboardInterrupt."""
    # Setup
    runner = CliRunner()
    mock_a2a_interface = MagicMock()
    mock_a2a_interface_class.return_value = mock_a2a_interface
    
    # Mock asyncio.run to raise KeyboardInterrupt
    mock_asyncio.run.side_effect = KeyboardInterrupt()
    
    # Execute
    result = runner.invoke(app, ["serve-a2a"])
    
    # Verify
    assert result.exit_code == 0
    mock_a2a_interface_class.assert_called_once()
    mock_asyncio.run.assert_called_once()
    assert "Starting A2A server" in result.stdout
    assert "A2A server stopped" in result.stdout