import os
import tomllib
import tomli_w

import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.errors import ConfigError

pytestmark = [pytest.mark.integration, pytest.mark.error_recovery]


def test_atomic_swap_and_invalid_config(tmp_path, monkeypatch):
    cfg = tmp_path / "cfg.toml"
    cfg.write_text(tomli_w.dumps({"agents": ["A"], "loops": 1, "search": {"backends": []}}))
    loader = ConfigLoader.new_for_tests(search_paths=[cfg])

    def fake_load(self):
        try:
            data = tomllib.loads(cfg.read_text())
        except tomllib.TOMLDecodeError as exc:  # pragma: no cover - via ConfigError
            raise ConfigError("invalid config") from exc
        model = ConfigModel.from_dict(data)
        self._config = model
        return model

    monkeypatch.setattr(ConfigLoader, "load_config", fake_load, raising=False)

    first = loader.load_config()
    assert first.agents == ["A"]

    tmp = tmp_path / "tmp.toml"
    tmp.write_text(tomli_w.dumps({"agents": ["B"], "loops": 1, "search": {"backends": []}}))
    os.replace(tmp, cfg)
    updated = loader.load_config()
    assert updated.agents == ["B"]

    cfg.write_text("agents = [")
    with pytest.raises(ConfigError):
        loader.load_config()
    assert loader.config.agents == ["B"]
    ConfigLoader.reset_instance()
