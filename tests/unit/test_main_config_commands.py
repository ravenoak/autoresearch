import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from autoresearch.main import app


@pytest.fixture
def mock_config_loader():
    """Create a mock ConfigLoader for testing."""
    return MagicMock()


def test_config_init_command(tmp_path):
    """Test the config init command."""
    runner = CliRunner()
    result = runner.invoke(app, ["config", "init", "--config-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "Configuration initialized successfully." in result.stdout


def test_config_init_command_force(tmp_path):
    """Test the config init command with force flag."""
    runner = CliRunner()
    result = runner.invoke(
        app, ["config", "init", "--config-dir", str(tmp_path), "--force"]
    )
    assert result.exit_code == 0
    assert "Configuration initialized successfully." in result.stdout


@pytest.mark.xfail(reason="Config validation not supported")
@patch("autoresearch.main.config_cli.ConfigLoader")
def test_config_validate_command_valid(
    mock_config_loader_class, mock_config_loader, tmp_path
):
    """Test the config validate command with valid configuration."""
    runner = CliRunner()
    cfg_path = tmp_path / "autoresearch.toml"
    cfg_path.write_text("[core]\nloops=1\n")
    mock_config_loader_class.return_value = mock_config_loader
    mock_config_loader.search_paths = [cfg_path]
    mock_config_loader.env_path = tmp_path / ".env"
    mock_config_loader.validate_config.return_value = (True, [])
    result = runner.invoke(app, ["config", "validate"])
    assert result.exit_code == 0
    mock_config_loader_class.assert_called_once()
    assert "Configuration is valid" in result.stdout


@pytest.mark.xfail(reason="Config validation not supported")
@patch("autoresearch.main.config_cli.ConfigLoader")
def test_config_validate_command_invalid(
    mock_config_loader_class, mock_config_loader, tmp_path
):
    """Test the config validate command with invalid configuration."""
    runner = CliRunner()
    cfg_path = tmp_path / "autoresearch.toml"
    cfg_path.write_text("[core]\nloops=1\n")
    mock_config_loader_class.return_value = mock_config_loader
    mock_config_loader.search_paths = [cfg_path]
    mock_config_loader.env_path = tmp_path / ".env"
    mock_config_loader.validate_config.return_value = (False, ["Error 1", "Error 2"])
    result = runner.invoke(app, ["config", "validate"])
    assert result.exit_code == 1
    mock_config_loader_class.assert_called_once()
    assert "Configuration is invalid" in result.stdout
    assert "Error 1" in result.stdout
    assert "Error 2" in result.stdout
