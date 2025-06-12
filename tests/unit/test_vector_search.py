from autoresearch.storage import StorageManager
from autoresearch.config import ConfigModel, StorageConfig, ConfigLoader


class DummyConn:
    def __init__(self):
        self.commands = []

    def execute(self, sql, params=None):
        self.commands.append(sql)
        return self

    def fetchall(self):
        return [("n1", [0.1, 0.2])]


def _mock_config():
    return ConfigModel(
        storage=StorageConfig(
            vector_extension=True,
            hnsw_m=8,
            hnsw_ef_construction=100,
            hnsw_metric="cosine",
        )
    )


def test_create_hnsw_index(monkeypatch):
    dummy = DummyConn()
    monkeypatch.setattr(StorageManager, "get_duckdb_conn", lambda: dummy)
    monkeypatch.setattr("autoresearch.storage._db_conn", dummy, raising=False)
    monkeypatch.setattr(
        ConfigLoader,
        "load_config",
        lambda self: _mock_config(),
    )
    ConfigLoader()._config = None

    StorageManager.create_hnsw_index()
    assert any("USING hnsw" in cmd for cmd in dummy.commands)


def test_vector_search_builds_query(monkeypatch):
    dummy = DummyConn()
    monkeypatch.setattr(StorageManager, "get_duckdb_conn", lambda: dummy)
    monkeypatch.setattr("autoresearch.storage._db_conn", dummy, raising=False)
    monkeypatch.setattr(
        ConfigLoader,
        "load_config",
        lambda self: _mock_config(),
    )
    ConfigLoader()._config = None

    results = StorageManager.vector_search([0.1, 0.2], k=3)
    assert results == [{"node_id": "n1", "embedding": [0.1, 0.2]}]
    assert any("<->" in cmd and "LIMIT 3" in cmd for cmd in dummy.commands)
