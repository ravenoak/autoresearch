# mypy: ignore-errors
import logging
import time
from autoresearch.logging_utils import configure_logging
from autoresearch.config.loader import ConfigLoader


def test_stop_watching_after_logging_shutdown(tmp_path):
    configure_logging()
    loader = ConfigLoader()
    loader.watch_paths.clear()
    loader.watch_paths.append(str(tmp_path / "config.toml"))
    loader.watch_changes()
    # ensure thread started
    time.sleep(0)
    logging.shutdown()
    # should not raise even though logging is shut down
    loader.stop_watching()
