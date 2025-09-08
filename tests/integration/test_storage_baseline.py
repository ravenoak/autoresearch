from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.storage import StorageContext, StorageManager, StorageState


def test_ram_budget_respects_baseline(tmp_path, monkeypatch):
    """Eviction uses memory delta from setup baseline."""
    cfg = ConfigModel(
        storage=StorageConfig(duckdb_path=str(tmp_path / "kg.duckdb")),
        ram_budget_mb=1,
        graph_eviction_policy="lru",
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    # Simulate high baseline memory before setup
    monkeypatch.setattr("autoresearch.storage._process_ram_mb", lambda: 1000)
    st = StorageState()
    ctx = StorageContext()
    StorageManager.setup(db_path=cfg.storage.duckdb_path, context=ctx, state=st)

    # Avoid ontology reasoning delays during persistence
    monkeypatch.setattr(
        "autoresearch.storage.run_ontology_reasoner", lambda *_, **__: None
    )

    # After setup memory increases slightly
    monkeypatch.setattr("autoresearch.storage._process_ram_mb", lambda: 1001)
    StorageManager.persist_claim({"id": "a", "type": "fact", "content": "c"})
    assert StorageManager.get_graph().number_of_nodes() == 1

    StorageManager.teardown(remove_db=True, context=ctx, state=st)
    StorageManager.state = StorageState()
    StorageManager.context = StorageContext()
    ConfigLoader()._config = None


def test_eviction_respects_baseline_without_reasoner(tmp_path, monkeypatch):
    """Eviction honors baseline when ontology reasoning is bypassed."""

    cfg = ConfigModel(
        storage=StorageConfig(duckdb_path=str(tmp_path / "kg.duckdb")),
        ram_budget_mb=1,
        graph_eviction_policy="lru",
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    # Establish baseline memory before setup
    monkeypatch.setattr("autoresearch.storage._process_ram_mb", lambda: 1000)
    st = StorageState()
    ctx = StorageContext()
    StorageManager.setup(db_path=cfg.storage.duckdb_path, context=ctx, state=st)

    # Skip ontology reasoning to avoid unrelated failures
    monkeypatch.setattr(
        "autoresearch.storage.run_ontology_reasoner", lambda *_, **__: None
    )

    # Sequence of RAM readings: under budget, then over budget, then back under
    ram_values = [0.5, 2.0, 0.5]

    def fake_ram_mb() -> float:
        return ram_values.pop(0) if ram_values else 0.5

    monkeypatch.setattr(StorageManager, "_current_ram_mb", fake_ram_mb)

    StorageManager.persist_claim({"id": "a", "type": "fact", "content": "a"})
    StorageManager.persist_claim({"id": "b", "type": "fact", "content": "b"})

    graph = StorageManager.get_graph()
    assert graph.number_of_nodes() == 1
    assert "b" in graph and "a" not in graph

    StorageManager.teardown(remove_db=True, context=ctx, state=st)
    StorageManager.state = StorageState()
    StorageManager.context = StorageContext()
    ConfigLoader()._config = None
