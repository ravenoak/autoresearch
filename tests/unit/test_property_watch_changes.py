import threading
from hypothesis import given, strategies as st, settings, HealthCheck
from autoresearch.config.loader import ConfigLoader


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(n=st.integers(min_value=1, max_value=5))
def test_watch_changes_idempotent(config_watcher, n):
    loader = ConfigLoader()
    for _ in range(n):
        loader.watch_changes()
    threads = [t for t in threading.enumerate() if t.name == "ConfigWatcher"]
    assert len(threads) <= 1
    loader.stop_watching()
