from collections import OrderedDict
import autoresearch.storage as storage
from autoresearch.storage import StorageManager


def test_touch_node_updates_lru(monkeypatch):
    monkeypatch.setattr(
        "autoresearch.storage._lru",
        OrderedDict([("a", 1), ("b", 2)]),
        raising=False,
    )
    StorageManager.touch_node("a")
    assert list(storage._lru.keys()) == ["b", "a"]


def test_clear_all(storage_manager):
    StorageManager.persist_claim({"id": "n1", "type": "fact", "content": "c"})
    StorageManager.clear_all()
    assert StorageManager.get_graph().number_of_nodes() == 0
    conn = StorageManager.get_duckdb_conn()
    assert conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0] == 0
