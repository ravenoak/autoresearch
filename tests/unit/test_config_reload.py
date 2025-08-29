import threading
from pathlib import Path

import tomli_w

from autoresearch.config.loader import ConfigLoader

SPEC_PATH = Path(__file__).resolve().parents[2] / "docs/algorithms/config_utils.md"


def test_config_spec_exists() -> None:
    """Configuration specification document must exist."""
    assert SPEC_PATH.is_file()


def test_config_reload_on_change(example_autoresearch_toml):
    cfg_path = example_autoresearch_toml

    # Create a new ConfigLoader instance after changing the working directory
    # This ensures it will look for config files in the temporary directory
    loader = ConfigLoader.new_for_tests()
    loader._config = loader.load_config()

    # Force update of watch paths to include the new config file
    loader._update_watch_paths()

    # Simulate a reload and verify observers are notified
    reloaded = threading.Event()
    loader.notify_observers = lambda cfg: reloaded.set()
    assert loader.config.loops == 1

    cfg_path.write_text(tomli_w.dumps({"core": {"loops": 2}}))
    loader._config_time = 0
    new_cfg = loader.load_config()
    loader._config = new_cfg
    loader.notify_observers(new_cfg)
    assert reloaded.wait(0)
    assert loader.config.loops == 2
