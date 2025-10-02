import time
from pathlib import Path

import tomllib
import tomli_w

import pytest
from fastapi.testclient import TestClient

import autoresearch.api as api
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel


@pytest.mark.integration
@pytest.mark.slow
def test_api_detects_config_file_change(
    example_autoresearch_toml: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg_file = example_autoresearch_toml
    cfg_file.write_text(tomli_w.dumps({"loops": 1}))

    def load_config(self: ConfigLoader) -> ConfigModel:
        data = tomllib.loads(cfg_file.read_text())
        data.setdefault("api", {})
        data["api"].setdefault("role_permissions", {"anonymous": ["config"]})
        return ConfigModel.from_dict(data)

    monkeypatch.setattr(ConfigLoader, "load_config", load_config, raising=False)
    loader = ConfigLoader.new_for_tests(search_paths=[cfg_file])
    app = api.create_app(loader)
    client = TestClient(app)

    assert client.get("/config").json()["loops"] == 1

    cfg_file.write_text(tomli_w.dumps({"loops": 2}))
    time.sleep(0.1)
    assert client.get("/config").json()["loops"] == 2
