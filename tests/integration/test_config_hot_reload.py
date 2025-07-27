import time
import tomli_w
from autoresearch.config import ConfigLoader


def test_config_hot_reload(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_path = tmp_path / "autoresearch.toml"
    cfg_path.write_text(tomli_w.dumps({"core": {"loops": 1}}))
    ConfigLoader.reset_instance()
    loader = ConfigLoader()
    events: list[int] = []

    def fake_watch(*paths, stop_event=None):
        yield {(str(cfg_path), 2)}
        stop_event.set()

    monkeypatch.setattr("autoresearch.config.watch", fake_watch)

    with loader.watching(lambda c: events.append(c.loops)):
        loader.load_config()
        cfg_path.write_text(tomli_w.dumps({"core": {"loops": 2}}))
        time.sleep(0.1)

    assert events and events[-1] == 2
