import os
import tomli_w

import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.errors import ConfigError

pytestmark = [pytest.mark.integration, pytest.mark.error_recovery]


def test_atomic_swap_and_invalid_config(tmp_path, caplog):
    cfg = tmp_path / "cfg.toml"
    cfg.write_text(
        tomli_w.dumps(
            {"core": {"agents": ["A"], "loops": 1}, "search": {"backends": []}}
        )
    )
    loader = ConfigLoader.new_for_tests(search_paths=[cfg])

    first = loader.load_config()
    loader._config = first
    assert loader.config.agents == ["A"]

    tmp = tmp_path / "tmp.toml"
    tmp.write_text(
        tomli_w.dumps(
            {"core": {"agents": ["B"], "loops": 1}, "search": {"backends": []}}
        )
    )
    os.replace(tmp, cfg)
    updated = loader.load_config()
    loader._config = updated
    assert loader.config.agents == ["B"]

    cfg.write_text("core = { agents = [")
    with caplog.at_level("ERROR"):
        with pytest.raises(ConfigError):
            loader.load_config()
    assert "Error loading config file" in caplog.text
    assert loader.config.agents == ["B"]
    ConfigLoader.reset_instance()


def test_live_reload_without_restart(tmp_path):
    cfg = tmp_path / "cfg.toml"
    cfg.write_text(
        tomli_w.dumps(
            {"core": {"agents": ["A"], "loops": 1}, "search": {"backends": []}}
        )
    )
    loader = ConfigLoader.new_for_tests(search_paths=[cfg])

    first = loader.load_config()
    loader._config = first
    assert loader.config.agents == ["A"]

    cfg.write_text(
        tomli_w.dumps(
            {"core": {"agents": ["B"], "loops": 1}, "search": {"backends": []}}
        )
    )
    updated = loader.load_config()
    loader._config = updated
    assert loader.config.agents == ["B"]
    assert ConfigLoader() is loader
    ConfigLoader.reset_instance()
