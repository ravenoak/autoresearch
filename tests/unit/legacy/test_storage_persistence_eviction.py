# mypy: ignore-errors
import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration import metrics
from autoresearch.storage import StorageManager


@pytest.mark.parametrize("policy", ["lru", "score", "hybrid"])
def test_persistence_and_eviction(storage_manager, tmp_path, monkeypatch, policy):
    cfg = ConfigModel(ram_budget_mb=1, graph_eviction_policy=policy)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None
    monkeypatch.setattr(StorageManager, "_current_ram_mb", lambda: 1000)

    start = metrics.EVICTION_COUNTER._value.get()
    claim = {"id": "p1", "type": "fact", "content": "c"}
    db_file = tmp_path / "kg.duckdb"
    monkeypatch.setenv("DUCKDB_PATH", str(db_file))
    StorageManager.persist_claim(claim)
    assert StorageManager.context.db_backend._path.endswith("kg.duckdb")
    assert "p1" not in StorageManager.get_graph().nodes
    assert metrics.EVICTION_COUNTER._value.get() >= start + 1
    assert "p1" not in StorageManager._access_frequency
