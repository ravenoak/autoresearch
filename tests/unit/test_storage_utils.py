from collections import OrderedDict
from unittest.mock import patch

import autoresearch.storage as storage
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.storage import StorageManager
import pytest
from typing import Any


def test_touch_node_updates_lru(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        storage.StorageManager.state,
        "lru",
        OrderedDict([("a", 1), ("b", 2)]),
        raising=False,
    )
    StorageManager.touch_node("a")
    assert list(storage.StorageManager.state.lru.keys()) == ["b", "a"]


def test_clear_all(ensure_duckdb_schema: Any) -> None:
    with patch("autoresearch.storage.run_ontology_reasoner") as mock_reasoner:
        mock_reasoner.return_value = None

        StorageManager.persist_claim({"id": "n1", "type": "fact", "content": "c"})
        StorageManager.clear_all()

        # Expect reasoning to be invoked once during persistence
        mock_reasoner.assert_called_once()

    assert StorageManager.get_graph().number_of_nodes() == 0
    conn = StorageManager.get_duckdb_conn()
    # Verify the nodes table is empty after clearing
    assert conn.execute("SELECT * FROM nodes").fetchall() == []


def test_initialize_storage_creates_tables(monkeypatch: pytest.MonkeyPatch) -> None:
    storage.teardown(remove_db=True)

    config = ConfigModel()
    config.search.context_aware.enabled = False
    config.storage.rdf_backend = "memory"
    config.storage.vector_extension = False

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: config)
    ConfigLoader()._config = None

    monkeypatch.setattr(storage.DuckDBStorageBackend, "_run_migrations", lambda self: None)

    ctx = storage.initialize_storage(":memory:")
    backend = ctx.db_backend
    assert backend is not None
    conn = backend.get_connection()
    tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    assert {"nodes", "edges", "embeddings", "metadata"}.issubset(tables)
