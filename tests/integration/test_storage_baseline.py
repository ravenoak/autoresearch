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

    # After setup memory increases slightly
    monkeypatch.setattr("autoresearch.storage._process_ram_mb", lambda: 1001)
    StorageManager.persist_claim({"id": "a", "type": "fact", "content": "c"})
    assert StorageManager.get_graph().number_of_nodes() == 1

    StorageManager.teardown(remove_db=True, context=ctx, state=st)
    StorageManager.state = StorageState()
    StorageManager.context = StorageContext()
    ConfigLoader()._config = None
