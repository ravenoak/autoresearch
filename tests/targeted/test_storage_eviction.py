"""Targeted tests for storage eviction and schema initialization."""

from threading import Thread

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.storage import (
    StorageContext,
    StorageManager,
    StorageState,
    initialize_storage,
)


def test_initialize_storage_idempotent() -> None:
    """`initialize_storage` can run repeatedly without side effects."""
    ctx = StorageContext()
    st = StorageState()
    initialize_storage(db_path=":memory:", context=ctx, state=st)
    first = ctx.db_backend._conn.execute("show tables").fetchall()
    initialize_storage(db_path=":memory:", context=ctx, state=st)
    second = ctx.db_backend._conn.execute("show tables").fetchall()
    assert first == second
    StorageManager.teardown(remove_db=True, context=ctx, state=st)
    StorageManager.state = StorageState()
    StorageManager.context = StorageContext()


def test_ram_budget_eviction(tmp_path, monkeypatch) -> None:
    """Concurrent writers respect the configured RAM budget."""
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

    def persist(idx: int) -> None:
        StorageManager.persist_claim({"id": f"c{idx}", "type": "fact", "content": "c"})

    threads = [Thread(target=persist, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert StorageManager.get_graph().number_of_nodes() == 0
    StorageManager.teardown(remove_db=True, context=ctx, state=st)
    StorageManager.state = StorageState()
    StorageManager.context = StorageContext()
    ConfigLoader()._config = None
