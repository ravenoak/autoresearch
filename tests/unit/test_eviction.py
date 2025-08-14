from datetime import timedelta

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration import metrics
from autoresearch.storage import StorageManager
from freezegun import freeze_time


def test_ram_eviction(storage_manager, monkeypatch):
    StorageManager.clear_all()
    monkeypatch.setattr(
        "autoresearch.storage.run_ontology_reasoner", lambda *_, **__: None
    )
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
    monkeypatch.setattr(
        "autoresearch.storage.run_ontology_reasoner", lambda *_, **__: None
    )
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
    monkeypatch.setattr(
        "autoresearch.storage.run_ontology_reasoner", lambda *_, **__: None
    )
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


def test_lru_eviction_sequence(storage_manager, monkeypatch):
    """Verify older nodes are evicted before newer ones with LRU policy."""
    StorageManager.clear_all()
    monkeypatch.setattr(
        "autoresearch.storage.run_ontology_reasoner", lambda *_, **__: None
    )
    config = ConfigModel(ram_budget_mb=1)
    config.search.context_aware.enabled = False
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: config)
    ConfigLoader()._config = None

    # Avoid eviction during setup
    monkeypatch.setattr(StorageManager, "_current_ram_mb", lambda: 0)

    with freeze_time() as frozen_time:
        StorageManager.persist_claim({"id": "c1", "type": "fact", "content": "a"})
        frozen_time.tick(delta=timedelta(seconds=1))
        StorageManager.persist_claim({"id": "c2", "type": "fact", "content": "b"})
        frozen_time.tick(delta=timedelta(seconds=1))
        StorageManager.persist_claim({"id": "c3", "type": "fact", "content": "c"})

    def fake_ram_factory():
        calls = {"n": 0}

        def fake_ram():
            calls["n"] += 1
            return 1000 if calls["n"] == 1 else 0

        return fake_ram

    monkeypatch.setattr(StorageManager, "_current_ram_mb", fake_ram_factory())
    StorageManager._enforce_ram_budget(1)
    graph = StorageManager.get_graph()
    assert "c1" not in graph.nodes
    assert "c2" in graph.nodes
    assert "c3" in graph.nodes

    monkeypatch.setattr(StorageManager, "_current_ram_mb", fake_ram_factory())
    StorageManager._enforce_ram_budget(1)
    graph = StorageManager.get_graph()
    assert "c2" not in graph.nodes
    assert "c3" in graph.nodes
