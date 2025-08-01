from __future__ import annotations

from pathlib import Path

import pytest

from autoresearch.config.loader import ConfigLoader


@pytest.fixture()
def config_loader() -> ConfigLoader:
    """Provide a ConfigLoader instance using the test configuration file."""
    loader = ConfigLoader.new_for_tests()
    test_cfg = Path(__file__).resolve().parents[1] / "data" / "autoresearch.toml"
    loader.search_paths = [test_cfg]
    loader._update_watch_paths()
    return loader


@pytest.fixture()
def config(config_loader: ConfigLoader):
    """Return the ConfigModel loaded from the test configuration."""
    return config_loader.load_config()
