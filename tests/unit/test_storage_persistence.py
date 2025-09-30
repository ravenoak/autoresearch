"""Regression tests for storage initialization and cleanup.

See docs/algorithms/storage_initialization.md for the specification.
"""

from __future__ import annotations

import duckdb

from autoresearch import storage
from autoresearch.extensions import VSSExtensionLoader
import pytest
from pathlib import Path


def test_initialize_creates_tables_and_teardown_removes_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure table creation runs and teardown removes the DB file."""

    db_file = tmp_path / "temp.duckdb"

    called = {"count": 0}
    orig_create = storage.DuckDBStorageBackend._create_tables

    def wrapped_create(self, skip_migrations: bool = False) -> None:
        called["count"] += 1
        return orig_create(self, skip_migrations)

    monkeypatch.setattr(storage.DuckDBStorageBackend, "_create_tables", wrapped_create)
    monkeypatch.setattr(
        storage.DuckDBStorageBackend, "_initialize_schema_version", lambda self: None
    )
    monkeypatch.setattr(storage.DuckDBStorageBackend, "_run_migrations", lambda self: None)
    monkeypatch.setattr(storage.DuckDBStorageBackend, "create_hnsw_index", lambda self: None)

    storage.teardown(remove_db=True)

    ctx = storage.initialize_storage(str(db_file))
    assert db_file.exists()
    first_calls = called["count"]

    storage.initialize_storage(str(db_file))
    assert called["count"] > first_calls

    storage.teardown(remove_db=True, context=ctx)
    assert not db_file.exists()


def test_initialize_handles_missing_extension(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Initialization proceeds when the vector extension cannot be loaded."""

    db_file = tmp_path / "temp.duckdb"
    called = {"count": 0}
    orig_create = storage.DuckDBStorageBackend._create_tables

    def wrapped_create(self, skip_migrations: bool = False) -> None:
        called["count"] += 1
        return orig_create(self, skip_migrations)

    monkeypatch.setattr(storage.DuckDBStorageBackend, "_create_tables", wrapped_create)
    monkeypatch.setattr(
        storage.DuckDBStorageBackend, "_initialize_schema_version", lambda self: None
    )
    monkeypatch.setattr(storage.DuckDBStorageBackend, "_run_migrations", lambda self: None)
    monkeypatch.setattr(storage.DuckDBStorageBackend, "create_hnsw_index", lambda self: None)
    monkeypatch.setattr(
        VSSExtensionLoader,
        "load_extension",
        lambda conn: (_ for _ in ()).throw(duckdb.Error("missing")),
    )

    storage.teardown(remove_db=True)
    ctx = storage.initialize_storage(str(db_file))
    assert db_file.exists()
    assert ctx.db_backend.has_vss() is False
    assert called["count"] >= 1
    ctx.db_backend._conn.execute("SELECT 1 FROM nodes LIMIT 1")
    storage.teardown(remove_db=True, context=ctx)
