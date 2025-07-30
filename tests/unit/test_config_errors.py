import pytest
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.xfail(reason="ConfigError handling not implemented")

from autoresearch.config import ConfigLoader, ConfigModel  # noqa: E402
from autoresearch.errors import ConfigError  # noqa: E402


def test_load_config_file_error(tmp_path, monkeypatch):
    """Test that ConfigError is raised when the config file can't be loaded."""
    ConfigLoader.reset_instance()
    monkeypatch.chdir(tmp_path)

    # Create an invalid TOML file
    config_path = tmp_path / "autoresearch.toml"
    config_path.write_text("invalid toml content")

    loader = ConfigLoader()

    # The current implementation logs the error but doesn't raise an exception
    # This test will fail until we implement the change
    with pytest.raises(ConfigError, match="Error loading config file"):
        loader.load_config()


def test_notify_observers_error():
    """Test that ConfigError is raised when an observer callback fails."""
    ConfigLoader.reset_instance()
    loader = ConfigLoader()

    # Create a mock observer that raises an exception
    mock_observer = MagicMock(side_effect=ValueError("Observer error"))
    loader.register_observer(mock_observer)

    # The current implementation logs the error but doesn't raise an exception
    # This test will fail until we implement the change
    with pytest.raises(ConfigError, match="Error in config observer"):
        loader.notify_observers(ConfigModel())


def test_watch_config_files_error(tmp_path, monkeypatch):
    """Test that ConfigError is raised when watching config files fails."""
    ConfigLoader.reset_instance()
    monkeypatch.chdir(tmp_path)

    # Create a config file that exists
    config_path = tmp_path / "autoresearch.toml"
    config_path.write_text("[core]\nloops = 1\n")

    loader = ConfigLoader()

    # Mock the watch function to raise an exception
    with patch("autoresearch.config.watch", side_effect=ValueError("Watch error")):
        # The current implementation logs the error but doesn't raise an exception
        # This test will fail until we implement the change
        with pytest.raises(ConfigError, match="Error in config watcher"):
            loader._watch_config_files()


def test_watch_config_reload_error(tmp_path, monkeypatch):
    """Test that ConfigError is raised when reloading config fails."""
    ConfigLoader.reset_instance()
    monkeypatch.chdir(tmp_path)

    # Create a config file that exists
    config_path = tmp_path / "autoresearch.toml"
    config_path.write_text("[core]\nloops = 1\n")

    loader = ConfigLoader()

    # Mock the watch function to return a change
    mock_watch = MagicMock()
    mock_watch.return_value = iter([{(1, str(config_path))}])

    # Mock load_config to raise an exception
    with patch("autoresearch.config.watch", mock_watch):
        with patch.object(
            loader, "load_config", side_effect=ValueError("Reload error")
        ):
            # The current implementation logs the error but doesn't raise an exception
            # This test will fail until we implement the change
            with pytest.raises(ConfigError, match="Error in config watcher"):
                loader._watch_config_files()


def test_reset_instance_error():
    """Test that ConfigError is raised when resetting the instance fails."""
    ConfigLoader.reset_instance()
    # Create a temporary instance and simulate failure stopping its watcher
    with ConfigLoader.temporary_instance() as loader:
        with patch.object(loader, "stop_watching", side_effect=ValueError("Stop error")):
            # The current implementation suppresses the exception
            # This test will fail until we implement the change
            with pytest.raises(ConfigError, match="Error stopping config watcher"):
                ConfigLoader.reset_instance()
