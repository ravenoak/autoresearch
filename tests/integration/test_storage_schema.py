from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from autoresearch.config import ConfigLoader, ConfigModel
from autoresearch.storage import (
    StorageContext,
    StorageState,
    initialize_storage,
    teardown,
)
from autoresearch.storage_backends import DuckDBStorageBackend
from autoresearch.storage_typing import (
    DuckDBConnectionProtocol,
    DuckDBCursorProtocol,
)
from autoresearch.storage_utils import initialize_schema_version_without_fetchone


@pytest.mark.parametrize("db_path", [":memory:", "disk"], ids=["memory", "disk"])
def test_initialize_storage_creates_tables(tmp_path: Path, db_path: str) -> None:
    """Required DuckDB tables exist after initialize_storage."""
    ConfigLoader()._config = None
    cfg: ConfigModel = ConfigLoader().config
    cfg.storage.vector_extension = False
    path = ":memory:" if db_path == ":memory:" else str(tmp_path / "kg.duckdb")
    if db_path != ":memory":
        cfg.storage.duckdb_path = path
    cfg.storage.rdf_path = str(tmp_path / "rdf_store")
    ConfigLoader()._config = cfg

    st: StorageState = StorageState()
    ctx: StorageContext = StorageContext()

    initialize_storage(path, context=ctx, state=st)
    try:
        assert ctx.db_backend is not None
        db_backend = ctx.db_backend
        conn: DuckDBConnectionProtocol = db_backend.get_connection()
        conn.execute("SELECT * FROM nodes")
        conn.execute("SELECT * FROM edges")
        conn.execute("SELECT * FROM embeddings")
        conn.execute("SELECT * FROM metadata")
    finally:
        teardown(remove_db=True, context=ctx, state=st)
        ConfigLoader()._config = None


def test_initialize_schema_version_without_fetchone() -> None:
    """Helper initializes schema version when cursor lacks fetchone."""
    backend = DuckDBStorageBackend()
    backend.setup(db_path=":memory:", skip_migrations=True)
    setup_conn = backend._conn
    if setup_conn is None:  # pragma: no cover - defensive
        raise AssertionError("DuckDB connection was not initialised")
    setup_conn.execute("DELETE FROM metadata WHERE key='schema_version'")

    class NoFetchOneResult:
        def __init__(self, rows: list[tuple[str, ...]]):
            self._rows = rows

        def fetchall(self) -> list[tuple[str, ...]]:
            return self._rows

        def fetchone(self) -> tuple[str, ...] | None:
            return self._rows[0] if self._rows else None

    class NoFetchOneConn:
        def __init__(self, conn: DuckDBConnectionProtocol):
            self._conn = conn

        def execute(
            self, sql: str, *args: Any, **kwargs: Any
        ) -> DuckDBCursorProtocol:
            if "schema_version" in sql and "SELECT" in sql:
                return NoFetchOneResult([])
            return self._conn.execute(sql, *args, **kwargs)

    connection = backend._conn
    if connection is None:  # pragma: no cover - defensive
        raise AssertionError("DuckDB connection was not initialised")
    proxy = NoFetchOneConn(connection)
    initialize_schema_version_without_fetchone(proxy)
    assert backend.get_schema_version() == 1
