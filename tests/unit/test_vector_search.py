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


class MockDuckDBBackend:
    def __init__(self, conn):
        self._conn = conn
        self._has_vss = True

    def create_hnsw_index(self):
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS embeddings_hnsw ON embeddings USING hnsw (embedding)"
        )

    def get_connection(self):
        return self._conn

    def has_vss(self):
        return self._has_vss

    def vector_search(self, query_embedding, k=5):
        self._conn.execute("SET hnsw_ef_search=10")
        vector_literal = f"[{', '.join(str(x) for x in query_embedding)}]"
        sql = (
            f"SELECT node_id, embedding FROM embeddings ORDER BY embedding <-> {vector_literal} LIMIT {k}"
        )
        self._conn.execute(sql)
        return [{"node_id": "n1", "embedding": [0.1, 0.2]}]


def _mock_config():
    return ConfigModel(
        storage=StorageConfig(
            vector_extension=True,
            hnsw_m=8,
            hnsw_ef_construction=100,
            hnsw_metric="cosine",
            vector_nprobe=10,
        )
    )


def test_create_hnsw_index(monkeypatch):
    dummy = DummyConn()
    mock_backend = MockDuckDBBackend(dummy)
    monkeypatch.setattr("autoresearch.storage._db_backend", mock_backend, raising=False)
    monkeypatch.setattr(
        ConfigLoader,
        "load_config",
        lambda self: _mock_config(),
    )
    ConfigLoader()._config = None

    StorageManager.create_hnsw_index()
    assert any("m=8" in cmd and "ef_construction=100" in cmd for cmd in dummy.commands)


def test_vector_search_builds_query(monkeypatch):
    dummy = DummyConn()
    mock_backend = MockDuckDBBackend(dummy)
    monkeypatch.setattr("autoresearch.storage._db_backend", mock_backend, raising=False)
    monkeypatch.setattr(
        ConfigLoader,
        "load_config",
        lambda self: _mock_config(),
    )
    # Mock _ensure_storage_initialized to do nothing
    monkeypatch.setattr(StorageManager, "_ensure_storage_initialized", lambda: None)
    # Mock has_vss to return True
    monkeypatch.setattr(StorageManager, "has_vss", lambda: True)
    ConfigLoader()._config = None

    results = StorageManager.vector_search([0.1, 0.2], k=3)
    assert results == [{"node_id": "n1", "embedding": [0.1, 0.2]}]
    assert any("SET hnsw_ef_search=10" in cmd for cmd in dummy.commands)
    assert any("<->" in cmd and "LIMIT 3" in cmd for cmd in dummy.commands)


def test_vector_search_uses_config_nprobe(monkeypatch):
    dummy = DummyConn()
    mock_backend = MockDuckDBBackend(dummy)
    monkeypatch.setattr("autoresearch.storage._db_backend", mock_backend, raising=False)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: _mock_config())
    monkeypatch.setattr(StorageManager, "_ensure_storage_initialized", lambda: None)
    monkeypatch.setattr(StorageManager, "has_vss", lambda: True)
    ConfigLoader()._config = None

    StorageManager.vector_search([0.1, 0.2], k=2)
    assert "SET hnsw_ef_search=10" in dummy.commands[0]


class FailingConn(DummyConn):
    def execute(self, sql, params=None):
        raise RuntimeError("db fail")


class FailingBackend(MockDuckDBBackend):
    def vector_search(self, query_embedding, k=5):
        raise RuntimeError("db fail")


def test_vector_search_failure(monkeypatch):
    dummy = FailingConn()
    mock_backend = FailingBackend(dummy)
    monkeypatch.setattr("autoresearch.storage._db_backend", mock_backend, raising=False)
    monkeypatch.setattr(
        ConfigLoader,
        "load_config",
        lambda self: _mock_config(),
    )
    # Mock _ensure_storage_initialized to do nothing
    monkeypatch.setattr(StorageManager, "_ensure_storage_initialized", lambda: None)
    # Mock has_vss to return True
    monkeypatch.setattr(StorageManager, "has_vss", lambda: True)
    ConfigLoader()._config = None

    # The vector_search method should raise a StorageError when the database fails
    from autoresearch.errors import StorageError
    import pytest

    with pytest.raises(StorageError) as excinfo:
        StorageManager.vector_search([0.0, 0.0], k=1)
    assert "Vector search failed" in str(excinfo.value)
    assert excinfo.value.__cause__ is not None
