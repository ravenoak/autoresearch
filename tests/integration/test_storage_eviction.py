from threading import Thread

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.orchestration import metrics
from autoresearch.storage import StorageContext, StorageManager, StorageState


def test_concurrent_eviction(tmp_path, monkeypatch):
    cfg = ConfigModel(
        storage=StorageConfig(duckdb_path=str(tmp_path / "kg.duckdb")),
        ram_budget_mb=1,
        graph_eviction_policy="lru",
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    st = StorageState()
    ctx = StorageContext()
    monkeypatch.setattr(StorageManager, "_current_ram_mb", lambda: 1000)
    StorageManager.setup(db_path=cfg.storage.duckdb_path, context=ctx, state=st)

    start = metrics.EVICTION_COUNTER._value.get()

    def persist(idx: int) -> None:
        StorageManager.persist_claim({"id": f"c{idx}", "type": "fact", "content": "c"})

    threads = [Thread(target=persist, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert StorageManager.get_graph().number_of_nodes() == 0
    assert metrics.EVICTION_COUNTER._value.get() >= start + 5

    StorageManager.teardown(remove_db=True, context=ctx, state=st)
    StorageManager.state = StorageState()
    StorageManager.context = StorageContext()
    ConfigLoader()._config = None
