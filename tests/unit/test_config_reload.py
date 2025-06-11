import time
import tomli_w

from autoresearch.config import ConfigLoader


def test_config_reload_on_change(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_path = tmp_path / "autoresearch.toml"
    cfg_path.write_text(tomli_w.dumps({"core": {"loops": 1}}))

    loader = ConfigLoader()
    loader.stop_watching()
    loader._config = loader.load_config()
    loader.watch_changes()
    try:
        assert loader.config.loops == 1
        cfg_path.write_text(tomli_w.dumps({"core": {"loops": 2}}))
        # Wait for watcher thread to pick up the change
        for _ in range(30):
            if loader.config.loops == 2:
                break
            time.sleep(0.1)
        assert loader.config.loops == 2
    finally:
        loader.stop_watching()
