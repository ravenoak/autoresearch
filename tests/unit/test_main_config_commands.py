import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from importlib.resources import files
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
    cfg = tmp_path / "autoresearch.toml"
    env = tmp_path / ".env"
    cfg.write_text("[core]\nloops=1\n")
    env.write_text("OPENAI_API_KEY=old\n")
    result = runner.invoke(
        app, ["config", "init", "--config-dir", str(tmp_path), "--force"]
    )
    assert result.exit_code == 0
    example_dir = files("autoresearch.examples")
    assert cfg.read_text(encoding="utf-8") == (
        example_dir / "autoresearch.toml"
    ).read_text(encoding="utf-8")
    assert env.read_text(encoding="utf-8") == (example_dir / ".env.example").read_text(
        encoding="utf-8"
    )
    assert "Configuration initialized successfully." in result.stdout


def test_config_validate_command_valid(mock_config_loader, tmp_path):
    """Test the config validate command with valid configuration."""
    runner = CliRunner()
    cfg_path = tmp_path / "autoresearch.toml"
    cfg_path.write_text("[core]\nloops=1\n")
    mock_config_loader.search_paths = [cfg_path]
    mock_config_loader.env_path = tmp_path / ".env"
    with (
        patch(
            "autoresearch.main.config_cli.ConfigLoader", return_value=mock_config_loader
        ) as mock_loader_class,
        patch(
            "autoresearch.main.config_cli.validate_config", return_value=(True, [])
        ) as mock_validate,
    ):
        result = runner.invoke(app, ["config", "validate"])
    assert result.exit_code == 0
    mock_loader_class.assert_called_once()
    mock_validate.assert_called_once_with(mock_config_loader)
    assert "Configuration is valid" in result.stdout


def test_config_validate_command_invalid(mock_config_loader, tmp_path):
    """Test the config validate command with invalid configuration."""
    runner = CliRunner()
    cfg_path = tmp_path / "autoresearch.toml"
    cfg_path.write_text("[core]\nloops=1\n")
    mock_config_loader.search_paths = [cfg_path]
    mock_config_loader.env_path = tmp_path / ".env"
    with (
        patch(
            "autoresearch.main.config_cli.ConfigLoader", return_value=mock_config_loader
        ) as mock_loader_class,
        patch(
            "autoresearch.main.config_cli.validate_config",
            return_value=(False, ["Error 1", "Error 2"]),
        ) as mock_validate,
    ):
        result = runner.invoke(app, ["config", "validate"])
    assert result.exit_code == 1
    mock_loader_class.assert_called_once()
    mock_validate.assert_called_once_with(mock_config_loader)
    assert "Configuration is invalid" in result.stdout
    assert "Error 1" in result.stdout
    assert "Error 2" in result.stdout
