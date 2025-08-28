import pytest

from autoresearch.config import ConfigLoader
from autoresearch.storage import (
    StorageContext,
    StorageState,
    initialize_storage,
    teardown,
)
from autoresearch.storage_backends import DuckDBStorageBackend


@pytest.mark.parametrize("db_path", [":memory:", "disk"], ids=["memory", "disk"])
def test_initialize_storage_creates_tables(tmp_path, db_path):
    """Required DuckDB tables exist after initialize_storage."""
    ConfigLoader()._config = None
    cfg = ConfigLoader().config
    cfg.storage.vector_extension = False
    path = ":memory:" if db_path == ":memory:" else str(tmp_path / "kg.duckdb")
    if db_path != ":memory:":
        cfg.storage.duckdb_path = path
    ConfigLoader()._config = cfg

    st = StorageState()
    ctx = StorageContext()

    initialize_storage(path, context=ctx, state=st)
    try:
        conn = ctx.db_backend.get_connection()  # type: ignore[union-attr]
        conn.execute("SELECT * FROM nodes")
        conn.execute("SELECT * FROM edges")
        conn.execute("SELECT * FROM embeddings")
        conn.execute("SELECT * FROM metadata")
    finally:
        teardown(remove_db=True, context=ctx, state=st)
        ConfigLoader()._config = None


def test_initialize_schema_version_without_fetchone(monkeypatch):
    """_initialize_schema_version works when DuckDB lacks fetchone."""
    backend = DuckDBStorageBackend()
    backend.setup(db_path=":memory:", skip_migrations=True)
    backend._conn.execute("DELETE FROM metadata WHERE key='schema_version'")
    original_execute = backend._conn.execute

    class NoFetchOneResult:
        def __init__(self, rows):
            self._rows = rows

        def fetchall(self) -> list[list[str]]:
            return self._rows

    def fake_execute(sql: str, *args, **kwargs):
        if "schema_version" in sql and "SELECT" in sql:
            return NoFetchOneResult([])
        return original_execute(sql, *args, **kwargs)

    monkeypatch.setattr(backend._conn, "execute", fake_execute)
    backend._initialize_schema_version()
    rows = backend._conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchall()
    assert rows and rows[0][0] == "1"
