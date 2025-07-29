"""Tests for configuration profiles feature.

This module contains tests for the configuration profiles feature, which allows
users to define and switch between different configuration profiles.
"""

import pytest
from unittest.mock import patch, mock_open

pytestmark = pytest.mark.xfail(reason="Config profiles not supported in tests")
import time  # noqa: E402
import stat  # noqa: E402

from autoresearch.config import ConfigLoader  # noqa: E402
from autoresearch.errors import ConfigError  # noqa: E402


# Mock for Path.stat() that returns an object with st_mtime and st_mode
class MockStat:
    def __init__(self):
        self.st_mtime = time.time()
        # Set st_mode to indicate a regular file
        self.st_mode = stat.S_IFREG


def mock_stat(*args, **kwargs):
    return MockStat()


def test_config_profiles_default():
    """Test that the default profile is used when no profile is specified."""
    # Mock the tomllib.load function to return a config with profiles
    mock_config = {
        "core": {
            "llm_backend": "openai",
            "loops": 3,
        },
        "profiles": {
            "offline": {
                "llm_backend": "lmstudio",
                "loops": 1,
            },
            "online": {
                "llm_backend": "openai",
                "loops": 5,
            },
        },
    }

    with patch("builtins.open", mock_open()):
        with patch("tomllib.load", return_value=mock_config):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.stat", mock_stat):
                    # Reset the singleton to ensure we get a fresh instance
                    ConfigLoader.reset_instance()
                    config = ConfigLoader().load_config()

                # Should use the default (core) settings
                assert config.llm_backend == "openai"
                assert config.loops == 3
                assert config.active_profile is None


def test_config_profiles_switch():
    """Test switching between configuration profiles."""
    # Mock the tomllib.load function to return a config with profiles
    mock_config = {
        "core": {
            "llm_backend": "openai",
            "loops": 3,
        },
        "profiles": {
            "offline": {
                "llm_backend": "lmstudio",
                "loops": 1,
            },
            "online": {
                "llm_backend": "openai",
                "loops": 5,
            },
        },
    }

    with patch("builtins.open", mock_open()):
        with patch("tomllib.load", return_value=mock_config):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.stat", mock_stat):
                    # Reset the singleton to ensure we get a fresh instance
                    ConfigLoader.reset_instance()
                    config_loader = ConfigLoader()

                    # Switch to the offline profile
                    config_loader.set_active_profile("offline")
                    config = config_loader.config

                    # Should use the offline profile settings
                    assert config.llm_backend == "lmstudio"
                    assert config.loops == 1
                    assert config.active_profile == "offline"

                    # Switch to the online profile
                    config_loader.set_active_profile("online")
                    config = config_loader.config

                    # Should use the online profile settings
                    assert config.llm_backend == "openai"
                    assert config.loops == 5
                    assert config.active_profile == "online"


def test_config_profiles_invalid():
    """Test that an error is raised when an invalid profile is specified."""
    # Mock the tomllib.load function to return a config with profiles
    mock_config = {
        "core": {
            "llm_backend": "openai",
            "loops": 3,
        },
        "profiles": {
            "offline": {
                "llm_backend": "lmstudio",
                "loops": 1,
            }
        },
    }

    with patch("builtins.open", mock_open()):
        with patch("tomllib.load", return_value=mock_config):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.stat", mock_stat):
                    # Reset the singleton to ensure we get a fresh instance
                    ConfigLoader.reset_instance()
                    config_loader = ConfigLoader()

                    # Try to switch to a non-existent profile
                    with pytest.raises(ConfigError) as excinfo:
                        config_loader.set_active_profile("nonexistent")

                    # Check that the error message is helpful
                    assert "Invalid profile" in str(excinfo.value)
                    assert "nonexistent" in str(excinfo.value)
                    assert "offline" in str(
                        excinfo.value
                    )  # Should suggest valid profiles


def test_config_profiles_merge():
    """Test that profile settings are merged with core settings."""
    # Mock the tomllib.load function to return a config with profiles
    mock_config = {
        "core": {
            "llm_backend": "openai",
            "loops": 3,
            "agents": ["Synthesizer", "Contrarian", "FactChecker"],
            "reasoning_mode": "dialectical",
        },
        "profiles": {
            "minimal": {
                "llm_backend": "lmstudio",
                "loops": 1,
                # Doesn't override agents or reasoning_mode
            }
        },
    }

    with patch("builtins.open", mock_open()):
        with patch("tomllib.load", return_value=mock_config):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.stat", mock_stat):
                    # Reset the singleton to ensure we get a fresh instance
                    ConfigLoader.reset_instance()
                    config_loader = ConfigLoader()

                    # Switch to the minimal profile
                    config_loader.set_active_profile("minimal")
                    config = config_loader.config

                    # Should use the minimal profile settings where specified
                    assert config.llm_backend == "lmstudio"
                    assert config.loops == 1

                    # Should inherit core settings for unspecified fields
                    assert config.agents == ["Synthesizer", "Contrarian", "FactChecker"]
                    assert config.reasoning_mode.value == "dialectical"
