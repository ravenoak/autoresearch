import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from autoresearch.main import app
from autoresearch.config.loader import ConfigLoader


@pytest.fixture
def mock_config_loader():
    """Create a mock ConfigLoader for testing."""
    mock_loader = MagicMock(spec=ConfigLoader)
    return mock_loader


@patch("autoresearch.main.ConfigLoader")
def test_config_init_command(mock_config_loader_class, mock_config_loader, tmp_path):
    """Test the config init command."""
    # Setup
    runner = CliRunner()
    mock_config_loader_class.return_value = mock_config_loader
    mock_config_loader.initialize_config_files.return_value = [
        "autoresearch.toml",
        ".env",
    ]

    # Execute
    result = runner.invoke(app, ["config", "init", "--config-dir", str(tmp_path)])

    # Verify
    assert result.exit_code == 0
    mock_config_loader_class.assert_called_once()
    mock_config_loader.initialize_config_files.assert_called_once()
    assert "Configuration files created" in result.stdout


@patch("autoresearch.main.ConfigLoader")
def test_config_init_command_force(
    mock_config_loader_class, mock_config_loader, tmp_path
):
    """Test the config init command with force flag."""
    # Setup
    runner = CliRunner()
    mock_config_loader_class.return_value = mock_config_loader
    mock_config_loader.initialize_config_files.return_value = [
        "autoresearch.toml",
        ".env",
    ]

    # Execute
    result = runner.invoke(
        app, ["config", "init", "--config-dir", str(tmp_path), "--force"]
    )

    # Verify
    assert result.exit_code == 0
    mock_config_loader_class.assert_called_once()
    mock_config_loader.initialize_config_files.assert_called_once_with(
        config_dir=str(tmp_path), force=True
    )
    assert "Configuration files created" in result.stdout


@patch("autoresearch.main.ConfigLoader")
def test_config_validate_command_valid(mock_config_loader_class, mock_config_loader):
    """Test the config validate command with valid configuration."""
    # Setup
    runner = CliRunner()
    mock_config_loader_class.return_value = mock_config_loader
    mock_config_loader.validate_config.return_value = (True, [])

    # Execute
    result = runner.invoke(app, ["config", "validate"])

    # Verify
    assert result.exit_code == 0
    mock_config_loader_class.assert_called_once()
    mock_config_loader.validate_config.assert_called_once()
    assert "Configuration is valid" in result.stdout


@patch("autoresearch.main.ConfigLoader")
def test_config_validate_command_invalid(mock_config_loader_class, mock_config_loader):
    """Test the config validate command with invalid configuration."""
    # Setup
    runner = CliRunner()
    mock_config_loader_class.return_value = mock_config_loader
    mock_config_loader.validate_config.return_value = (False, ["Error 1", "Error 2"])

    # Execute
    result = runner.invoke(app, ["config", "validate"])

    # Verify
    assert result.exit_code == 1
    mock_config_loader_class.assert_called_once()
    mock_config_loader.validate_config.assert_called_once()
    assert "Configuration is invalid" in result.stdout
    assert "Error 1" in result.stdout
    assert "Error 2" in result.stdout


@patch("autoresearch.main.ConfigLoader")
def test_start_watcher_command(mock_config_loader_class, mock_config_loader):
    """Test the start-watcher command."""
    # Setup
    runner = CliRunner()
    mock_config_loader_class.return_value = mock_config_loader

    # Mock the start_watcher method to raise KeyboardInterrupt after being called
    mock_config_loader.start_watcher.side_effect = KeyboardInterrupt()

    # Execute
    result = runner.invoke(app, ["start-watcher"])

    # Verify
    assert result.exit_code == 0
    mock_config_loader_class.assert_called_once()
    mock_config_loader.start_watcher.assert_called_once()
    assert "Starting configuration watcher" in result.stdout
    assert "Watcher stopped" in result.stdout


@patch("autoresearch.main.ConfigLoader")
def test_start_watcher_command_with_vss_path(
    mock_config_loader_class, mock_config_loader
):
    """Test the start-watcher command with VSS path."""
    # Setup
    runner = CliRunner()
    mock_config_loader_class.return_value = mock_config_loader

    # Mock the start_watcher method to raise KeyboardInterrupt after being called
    mock_config_loader.start_watcher.side_effect = KeyboardInterrupt()

    # Execute
    result = runner.invoke(app, ["start-watcher", "--vss-path", "/path/to/vss.so"])

    # Verify
    assert result.exit_code == 0
    mock_config_loader_class.assert_called_once()
    mock_config_loader.start_watcher.assert_called_once_with(
        vss_path="/path/to/vss.so", no_vss=False
    )
    assert "Starting configuration watcher" in result.stdout


@patch("autoresearch.main.ConfigLoader")
def test_start_watcher_command_no_vss(mock_config_loader_class, mock_config_loader):
    """Test the start-watcher command with no-vss flag."""
    # Setup
    runner = CliRunner()
    mock_config_loader_class.return_value = mock_config_loader

    # Mock the start_watcher method to raise KeyboardInterrupt after being called
    mock_config_loader.start_watcher.side_effect = KeyboardInterrupt()

    # Execute
    result = runner.invoke(app, ["start-watcher", "--no-vss"])

    # Verify
    assert result.exit_code == 0
    mock_config_loader_class.assert_called_once()
    mock_config_loader.start_watcher.assert_called_once_with(vss_path=None, no_vss=True)
    assert "Starting configuration watcher" in result.stdout
