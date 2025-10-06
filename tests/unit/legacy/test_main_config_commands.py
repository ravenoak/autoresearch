# mypy: ignore-errors
from __future__ import annotations

import shutil
from importlib.abc import Traversable
from pathlib import Path
from unittest.mock import MagicMock, patch

import importlib.resources as importlib_resources
import pytest
from typer.testing import CliRunner

from autoresearch.main import app


pytestmark = pytest.mark.usefixtures("dummy_storage")


@pytest.fixture
def mock_config_loader() -> MagicMock:
    """Create a mock ConfigLoader for testing."""
    return MagicMock()


@pytest.fixture
def example_resources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Provide temporary example config files."""
    src_dir = importlib_resources.files("autoresearch.examples")
    temp_dir = tmp_path / "examples"
    with importlib_resources.as_file(src_dir) as resolved:
        shutil.copytree(resolved, temp_dir)

    def _files(package: str) -> Traversable:
        if package == "autoresearch.examples":
            return temp_dir
        return importlib_resources.files(package)

    monkeypatch.setattr(importlib_resources, "files", _files)
    return temp_dir


def test_config_init_command(tmp_path: Path, example_resources: Path) -> None:
    """Test the config init command."""
    runner = CliRunner()
    result = runner.invoke(
        app, ["config", "init", "--config-dir", str(tmp_path)], prog_name="autoresearch"
    )
    assert result.exit_code == 0
    assert "Configuration initialized successfully." in result.stdout


def test_config_init_command_force(
    example_autoresearch_toml: Path,
    example_env_file: Path,
    example_resources: Path,
) -> None:
    """Test the config init command with force flag."""
    runner = CliRunner()
    cfg = example_autoresearch_toml
    env = example_env_file
    result = runner.invoke(
        app,
        ["config", "init", "--config-dir", str(cfg.parent), "--force"],
        prog_name="autoresearch",
    )
    assert result.exit_code == 0
    example_dir = example_resources
    assert cfg.read_text(encoding="utf-8") == (example_dir / "autoresearch.toml").read_text(
        encoding="utf-8"
    )
    assert env.read_text(encoding="utf-8") == (example_dir / ".env.example").read_text(
        encoding="utf-8"
    )
    assert "Configuration initialized successfully." in result.stdout


def test_config_validate_command_valid(
    mock_config_loader: MagicMock,
    example_autoresearch_toml: Path,
    example_env_file: Path,
) -> None:
    """Test the config validate command with valid configuration."""
    runner = CliRunner()
    cfg_path = example_autoresearch_toml
    mock_config_loader.search_paths = [cfg_path]
    mock_config_loader.env_path = example_env_file
    with (
        patch(
            "autoresearch.main.config_cli.ConfigLoader", return_value=mock_config_loader
        ) as mock_loader_class,
        patch(
            "autoresearch.main.config_cli.validate_config", return_value=(True, [])
        ) as mock_validate,
    ):
        result = runner.invoke(app, ["config", "validate"], prog_name="autoresearch")
    assert result.exit_code == 0
    mock_loader_class.assert_called_once()
    mock_validate.assert_called_once_with(mock_config_loader)
    assert "Configuration is valid" in result.stdout


def test_config_validate_command_invalid(
    mock_config_loader: MagicMock,
    example_autoresearch_toml: Path,
    example_env_file: Path,
) -> None:
    """Test the config validate command with invalid configuration."""
    runner = CliRunner()
    cfg_path = example_autoresearch_toml
    mock_config_loader.search_paths = [cfg_path]
    mock_config_loader.env_path = example_env_file
    with (
        patch(
            "autoresearch.main.config_cli.ConfigLoader", return_value=mock_config_loader
        ) as mock_loader_class,
        patch(
            "autoresearch.main.config_cli.validate_config",
            return_value=(False, ["Error 1", "Error 2"]),
        ) as mock_validate,
    ):
        result = runner.invoke(app, ["config", "validate"], prog_name="autoresearch")
    assert result.exit_code == 1
    mock_loader_class.assert_called_once()
    mock_validate.assert_called_once_with(mock_config_loader)
    assert "Configuration is invalid" in result.stdout
    assert "Error 1" in result.stdout
    assert "Error 2" in result.stdout
