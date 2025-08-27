import pytest

from autoresearch.storage import (
    StorageContext,
    StorageState,
    initialize_storage,
    teardown,
)
from autoresearch.config import ConfigLoader


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
