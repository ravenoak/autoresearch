from datetime import timedelta

from freezegun import freeze_time

from autoresearch import storage
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration import metrics
from autoresearch.storage import StorageManager


def test_ram_eviction(storage_manager, monkeypatch):
    StorageManager.clear_all()
    monkeypatch.setattr("autoresearch.storage.run_ontology_reasoner", lambda *_, **__: None)
    config = ConfigModel(ram_budget_mb=1)
    config.search.context_aware.enabled = False
    config.storage.rdf_backend = "memory"
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
    monkeypatch.setattr("autoresearch.storage.run_ontology_reasoner", lambda *_, **__: None)
    config = ConfigModel(ram_budget_mb=1, graph_eviction_policy="score")
    config.search.context_aware.enabled = False
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: config)
    ConfigLoader()._config = None
    monkeypatch.setattr(StorageManager, "_current_ram_mb", lambda: 0)
    StorageManager.persist_claim({"id": "low", "type": "fact", "content": "a", "confidence": 0.1})
    StorageManager.persist_claim({"id": "high", "type": "fact", "content": "b", "confidence": 0.9})
    calls = [0]

    def fake_ram():
        calls[0] += 1
        return 1000 if calls[0] == 1 else 0

    monkeypatch.setattr(StorageManager, "_current_ram_mb", fake_ram)
    StorageManager._enforce_ram_budget(1)
    graph = StorageManager.get_graph()
    assert "low" not in graph.nodes
    assert "high" in graph.nodes


def test_lru_eviction_order(monkeypatch, tmp_path):
    storage.teardown(remove_db=True)
    db_file = tmp_path / "kg.duckdb"
    config = ConfigModel(ram_budget_mb=1)
    config.search.context_aware.enabled = False
    config.storage.rdf_backend = "memory"
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: config)
    ConfigLoader()._config = None
    storage.setup(str(db_file))
    StorageManager.clear_all()
    monkeypatch.setattr("autoresearch.storage.run_ontology_reasoner", lambda *_, **__: None)
    monkeypatch.setattr(StorageManager, "_current_ram_mb", lambda: 0)
    with freeze_time("2024-01-01") as frozen_time:
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
    monkeypatch.setattr("autoresearch.storage.run_ontology_reasoner", lambda *_, **__: None)
    config = ConfigModel(ram_budget_mb=1)
    config.search.context_aware.enabled = False
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: config)
    ConfigLoader()._config = None

    # Avoid eviction during setup
    monkeypatch.setattr(StorageManager, "_current_ram_mb", lambda: 0)

    with freeze_time("2024-01-01") as frozen_time:
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


def test_initialize_storage_in_memory(monkeypatch):
    """Regression test ensuring in-memory DuckDB creates required tables."""

    storage.teardown(remove_db=True)

    config = ConfigModel()
    config.search.context_aware.enabled = False
    config.storage.rdf_backend = "memory"
    config.storage.vector_extension = False

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: config)
    ConfigLoader()._config = None

    # DuckDB <1.0 lacks fetchone; skip schema version initialization
    monkeypatch.setattr(
        storage.DuckDBStorageBackend, "_initialize_schema_version", lambda self: None
    )
    monkeypatch.setattr(storage.DuckDBStorageBackend, "_run_migrations", lambda self: None)

    called = {"flag": False}

    original_create = storage.DuckDBStorageBackend._create_tables

    def wrapped_create(self, skip_migrations: bool = False) -> None:
        called["flag"] = True
        return original_create(self, skip_migrations)

    monkeypatch.setattr(storage.DuckDBStorageBackend, "_create_tables", wrapped_create)

    ctx = storage.initialize_storage(":memory:")
    backend = ctx.db_backend
    assert backend is not None
    assert called["flag"]


def test_initialize_storage_file_path(monkeypatch, tmp_path):
    """Ensure initializing with a file path creates missing tables."""

    storage.teardown(remove_db=True)
    db_file = tmp_path / "kg.duckdb"

    config = ConfigModel()
    config.search.context_aware.enabled = False
    config.storage.rdf_backend = "memory"
    config.storage.vector_extension = False

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: config)
    ConfigLoader()._config = None

    monkeypatch.setattr(
        storage.DuckDBStorageBackend,
        "_initialize_schema_version",
        lambda self: None,
    )
    monkeypatch.setattr(storage.DuckDBStorageBackend, "_run_migrations", lambda self: None)

    called = {"flag": False}
    original_create = storage.DuckDBStorageBackend._create_tables

    def wrapped_create(self, skip_migrations: bool = False) -> None:
        called["flag"] = True
        return original_create(self, skip_migrations)

    monkeypatch.setattr(storage.DuckDBStorageBackend, "_create_tables", wrapped_create)

    ctx = storage.initialize_storage(str(db_file))
    backend = ctx.db_backend
    assert backend is not None
    assert called["flag"]
