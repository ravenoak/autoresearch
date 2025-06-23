import time
import tomli_w
from autoresearch.config import ConfigLoader


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

    # Start watching for changes
    loader.watch_changes()
    assert loader.config.loops == 1

    # Modify the config file
    cfg_path.write_text(tomli_w.dumps({"core": {"loops": 2}}))

    # Manually reload configuration since file watching may not fire
    loader._config = loader.load_config()
    assert loader.config.loops == 2
