import threading
import tomli_w
from autoresearch.config.loader import ConfigLoader


def test_config_reload_on_change(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_path = tmp_path / "autoresearch.toml"
    cfg_path.write_text(tomli_w.dumps({"core": {"loops": 1}}))

    # Create a new ConfigLoader instance after changing the working directory
    # This ensures it will look for config files in the temporary directory
    loader = ConfigLoader()
    loader._config = loader.load_config()

    # Force update of watch paths to include the new config file
    loader._update_watch_paths()

    # Start watching for changes and wait for reload via callback
    reloaded = threading.Event()
    loader.watch_changes(lambda cfg: reloaded.set())
    assert loader.config.loops == 1

    cfg_path.write_text(tomli_w.dumps({"core": {"loops": 2}}))
    assert reloaded.wait(2)
    assert loader.config.loops == 2
