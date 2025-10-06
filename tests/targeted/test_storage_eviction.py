"""Targeted tests for storage eviction and schema initialization."""

from pathlib import Path
from threading import Thread

import pytest  # noqa: E402
pytestmark = pytest.mark.skip("requires storage extras")
from autoresearch.config.loader import ConfigLoader  # noqa: E402
from autoresearch.config.models import ConfigModel, StorageConfig  # noqa: E402
from autoresearch.storage import (  # noqa: E402
    StorageContext,
    StorageManager,
    StorageState,
    initialize_storage,
)
from autoresearch.storage_backends import DuckDBStorageBackend  # noqa: E402


def test_initialize_storage_idempotent() -> None:
    """`initialize_storage` can run repeatedly without side effects."""
    ctx = StorageContext()
    st = StorageState()
    initialize_storage(db_path=":memory:", context=ctx, state=st)
    db_backend = ctx.db_backend
    assert isinstance(db_backend, DuckDBStorageBackend)
    assert db_backend._conn is not None
    first = db_backend._conn.execute("show tables").fetchall()
    initialize_storage(db_path=":memory:", context=ctx, state=st)
    db_backend_second = ctx.db_backend
    assert isinstance(db_backend_second, DuckDBStorageBackend)
    assert db_backend_second._conn is not None
    second = db_backend_second._conn.execute("show tables").fetchall()
    assert first == second
    StorageManager.teardown(remove_db=True, context=ctx, state=st)
    StorageManager.state = StorageState()
    StorageManager.context = StorageContext()


def test_ram_budget_eviction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Concurrent writers respect the configured RAM budget."""
    cfg = ConfigModel(
        storage=StorageConfig(
            duckdb_path=str(tmp_path / "kg.duckdb"),
            vector_extension=False,
        ),
        ram_budget_mb=1,
        graph_eviction_policy="lru",
    )
    ConfigLoader.reset_instance()
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


def test_deterministic_eviction_across_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Eviction leaves a deterministic graph across runs."""
    cfg = ConfigModel(
        storage=StorageConfig(
            duckdb_path=str(tmp_path / "kg.duckdb"),
            vector_extension=False,
        ),
        ram_budget_mb=1,
        graph_eviction_policy="lru",
    )
    ConfigLoader.reset_instance()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    def run_once() -> int:
        st = StorageState()
        ctx = StorageContext()
        monkeypatch.setattr(StorageManager, "_current_ram_mb", lambda: 1000)
        StorageManager.setup(db_path=cfg.storage.duckdb_path, context=ctx, state=st)

        def persist(idx: int) -> None:
            StorageManager.persist_claim(
                {"id": f"c{idx}", "type": "fact", "content": "c"}
            )
            StorageManager._enforce_ram_budget(cfg.ram_budget_mb)

        threads = [Thread(target=persist, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        remaining = StorageManager.get_graph().number_of_nodes()
        StorageManager.teardown(remove_db=True, context=ctx, state=st)
        StorageManager.state = StorageState()
        StorageManager.context = StorageContext()
        return remaining

    results = [run_once() for _ in range(2)]
    assert results == [0, 0]
    ConfigLoader()._config = None
