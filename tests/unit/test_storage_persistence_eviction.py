from autoresearch.storage import StorageManager
from autoresearch.config import ConfigModel, ConfigLoader
from autoresearch.orchestration import metrics


def test_persistence_and_eviction(storage_manager, tmp_path, monkeypatch):
    cfg = ConfigModel(ram_budget_mb=1)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None
    monkeypatch.setattr(StorageManager, "_current_ram_mb", lambda: 1000)

    start = metrics.EVICTION_COUNTER._value.get()
    claim = {"id": "p1", "type": "fact", "content": "c"}
    StorageManager.persist_claim(claim)

    db_file = tmp_path / "kg.duckdb"
    assert db_file.exists()
    conn = StorageManager.get_duckdb_conn()
    result = conn.execute(
        "SELECT COUNT(*) FROM nodes WHERE id='p1'"
    ).fetchone()[0]
    assert result == 1
    assert "p1" not in StorageManager.get_graph().nodes
    assert metrics.EVICTION_COUNTER._value.get() >= start + 1
