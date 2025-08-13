
from datetime import timedelta

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration import metrics
from autoresearch.storage import StorageManager
from freezegun import freeze_time


def test_ram_eviction(storage_manager, monkeypatch):
    StorageManager.clear_all()
    config = ConfigModel(ram_budget_mb=1)
    config.search.context_aware.enabled = False
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: config)
    # reload config property
    ConfigLoader()._config = None

    start = metrics.EVICTION_COUNTER._value.get()
    claim = {"id": "c1", "type": "fact", "content": "a"}
    StorageManager.persist_claim(claim)
    assert metrics.EVICTION_COUNTER._value.get() >= start + 1
    assert "c1" not in StorageManager.get_graph().nodes


def test_score_eviction(storage_manager, monkeypatch):
    StorageManager.clear_all()
    config = ConfigModel(ram_budget_mb=1, graph_eviction_policy="score")
    config.search.context_aware.enabled = False
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: config)
    ConfigLoader()._config = None
    monkeypatch.setattr(StorageManager, "_current_ram_mb", lambda: 0)
    StorageManager.persist_claim(
        {"id": "low", "type": "fact", "content": "a", "confidence": 0.1}
    )
    StorageManager.persist_claim(
        {"id": "high", "type": "fact", "content": "b", "confidence": 0.9}
    )
    calls = [0]

    def fake_ram():
        calls[0] += 1
        return 1000 if calls[0] == 1 else 0

    monkeypatch.setattr(StorageManager, "_current_ram_mb", fake_ram)
    StorageManager._enforce_ram_budget(1)
    graph = StorageManager.get_graph()
    assert "low" not in graph.nodes
    assert "high" in graph.nodes


def test_lru_eviction_order(storage_manager, monkeypatch):
    StorageManager.clear_all()
    from autoresearch import storage

    storage.StorageManager.state.lru.clear()
    config = ConfigModel(ram_budget_mb=1)
    config.search.context_aware.enabled = False
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: config)
    ConfigLoader()._config = None
    monkeypatch.setattr(StorageManager, "_current_ram_mb", lambda: 0)
    with freeze_time() as frozen_time:
        StorageManager.persist_claim({"id": "c1", "type": "fact", "content": "a"})
        frozen_time.tick(delta=timedelta(seconds=1))
        StorageManager.persist_claim({"id": "c2", "type": "fact", "content": "b"})
    calls = [0]

    def fake_ram():
        calls[0] += 1
        return 1000 if calls[0] == 1 else 0

    monkeypatch.setattr(StorageManager, "_current_ram_mb", fake_ram)
    StorageManager._enforce_ram_budget(1)
    graph = StorageManager.get_graph()
    assert "c1" not in graph.nodes
    assert "c2" in graph.nodes
