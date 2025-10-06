# mypy: ignore-errors
import tomllib
import tomli_w

import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel

pytestmark = [pytest.mark.integration, pytest.mark.slow]


def test_loader_reload_on_file_change(example_autoresearch_toml, monkeypatch):
    cfg_file = example_autoresearch_toml
    cfg_file.write_text(tomli_w.dumps({"loops": 1}))

    def load_config(self):
        data = tomllib.loads(cfg_file.read_text())
        return ConfigModel.from_dict(data)

    monkeypatch.setattr(ConfigLoader, "load_config", load_config, raising=False)
    loader = ConfigLoader.new_for_tests(search_paths=[cfg_file])

    first = loader.load_config()
    loader._config = first
    assert loader.config.loops == 1

    cfg_file.write_text(tomli_w.dumps({"loops": 2}))
    loader._config = loader.load_config()
    assert loader.config.loops == 2
