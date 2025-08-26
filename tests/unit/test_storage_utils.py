from collections import OrderedDict
from unittest.mock import patch

import autoresearch.storage as storage
from autoresearch.config.models import ConfigModel
from autoresearch.storage import StorageManager


def test_touch_node_updates_lru(monkeypatch):
    monkeypatch.setattr(
        storage.StorageManager.state,
        "lru",
        OrderedDict([("a", 1), ("b", 2)]),
        raising=False,
    )
    StorageManager.touch_node("a")
    assert list(storage.StorageManager.state.lru.keys()) == ["b", "a"]


def test_clear_all(storage_manager):
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


def test_initialize_storage_persistent(tmp_path, monkeypatch):
    """Ensure initialize_storage creates tables for file-backed DBs."""

    storage.teardown(remove_db=True)
    db_file = tmp_path / "kg.duckdb"

    config = ConfigModel()
    config.search.context_aware.enabled = False
    config.storage.vector_extension = False
    config.storage.rdf_backend = "memory"
    monkeypatch.setattr(storage.ConfigLoader, "load_config", lambda self: config)
    storage.ConfigLoader()._config = None

    monkeypatch.setattr(
        storage.DuckDBStorageBackend, "_initialize_schema_version", lambda self: None
    )
    monkeypatch.setattr(storage.DuckDBStorageBackend, "_run_migrations", lambda self: None)

    called = {"flag": False}
    orig_create = storage.DuckDBStorageBackend._create_tables

    def wrapped_create(self, skip_migrations: bool = False) -> None:
        called["flag"] = True
        return orig_create(self, skip_migrations)

    monkeypatch.setattr(storage.DuckDBStorageBackend, "_create_tables", wrapped_create)

    storage.initialize_storage(str(db_file))

    assert called["flag"]
