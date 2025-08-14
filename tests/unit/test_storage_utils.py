from collections import OrderedDict
from unittest.mock import patch

import autoresearch.storage as storage
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
