from autoresearch.storage import StorageManager
from autoresearch.config import ConfigModel, ConfigLoader
from autoresearch.orchestration import metrics


def test_ram_eviction(monkeypatch):
    StorageManager.clear_all()
    config = ConfigModel(ram_budget_mb=1)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: config)
    # reload config property
    ConfigLoader()._config = None

    start = metrics.EVICTION_COUNTER._value.get()
    claim = {"id": "c1", "type": "fact", "content": "a"}
    StorageManager.persist_claim(claim)
    assert metrics.EVICTION_COUNTER._value.get() >= start + 1
    assert "c1" not in StorageManager.get_graph().nodes

