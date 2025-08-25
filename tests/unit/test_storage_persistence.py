"""Regression tests for storage initialization and cleanup."""

from __future__ import annotations

from autoresearch import storage


def test_initialize_creates_tables_and_teardown_removes_file(tmp_path, monkeypatch):
    """Ensure table creation runs and teardown removes the DB file."""

    db_file = tmp_path / "temp.duckdb"

    called = {"flag": False}
    orig_create = storage.DuckDBStorageBackend._create_tables

    def wrapped_create(self, skip_migrations: bool = False) -> None:
        called["flag"] = True
        return orig_create(self, skip_migrations)

    monkeypatch.setattr(storage.DuckDBStorageBackend, "_create_tables", wrapped_create)
    monkeypatch.setattr(
        storage.DuckDBStorageBackend, "_initialize_schema_version", lambda self: None
    )
    monkeypatch.setattr(storage.DuckDBStorageBackend, "_run_migrations", lambda self: None)
    monkeypatch.setattr(storage.DuckDBStorageBackend, "create_hnsw_index", lambda self: None)

    ctx = storage.initialize_storage(str(db_file))
    assert called["flag"]

    storage.teardown(remove_db=True, context=ctx)
    assert not db_file.exists()
