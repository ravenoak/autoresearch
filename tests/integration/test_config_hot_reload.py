import tomli_w
import tomllib
from types import SimpleNamespace

from autoresearch.config import ConfigLoader


def test_config_hot_reload(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_path = tmp_path / "autoresearch.toml"
    cfg_path.write_text(tomli_w.dumps({"core": {"loops": 1}}))
    ConfigLoader.reset_instance()

    def fake_load(self):
        data = tomllib.loads(cfg_path.read_text())
        return SimpleNamespace(loops=data["core"]["loops"])

    monkeypatch.setattr(ConfigLoader, "load_config", fake_load, raising=False)
    loader = ConfigLoader()
    events: list[int] = []

    events.append(loader.load_config().loops)
    cfg_path.write_text(tomli_w.dumps({"core": {"loops": 2}}))
    events.append(loader.load_config().loops)

    assert events[-1] == 2
