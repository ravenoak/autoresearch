from threading import Thread

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.storage import StorageContext, StorageManager, StorageState


def _setup(tmp_path, monkeypatch, ram_budget):
    cfg = ConfigModel(
        storage=StorageConfig(duckdb_path=str(tmp_path / "kg.duckdb")),
        ram_budget_mb=ram_budget,
        graph_eviction_policy="lru",
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    st = StorageState()
    ctx = StorageContext()
    StorageManager.setup(db_path=cfg.storage.duckdb_path, context=ctx, state=st)
    return cfg, st, ctx


def _teardown(st, ctx):
    StorageManager.teardown(remove_db=True, context=ctx, state=st)
    StorageManager.state = StorageState()
    StorageManager.context = StorageContext()
    ConfigLoader()._config = None


def test_concurrent_writes(tmp_path, monkeypatch):
    cfg, st, ctx = _setup(tmp_path, monkeypatch, ram_budget=50)

    def persist(idx: int) -> None:
        StorageManager.persist_claim({"id": f"c{idx}", "type": "fact", "content": "c"})

    threads = [Thread(target=persist, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert StorageManager.get_graph().number_of_nodes() == 5
    _teardown(st, ctx)


def test_concurrent_eviction(tmp_path, monkeypatch):
    cfg, st, ctx = _setup(tmp_path, monkeypatch, ram_budget=1)
    monkeypatch.setattr(StorageManager, "_current_ram_mb", lambda: 1000)

    def persist(idx: int) -> None:
        StorageManager.persist_claim({"id": f"c{idx}", "type": "fact", "content": "c"})
        StorageManager._enforce_ram_budget(cfg.ram_budget_mb)

    threads = [Thread(target=persist, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert StorageManager.get_graph().number_of_nodes() == 0
    _teardown(st, ctx)
