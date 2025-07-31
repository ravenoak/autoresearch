from unittest.mock import MagicMock
import networkx as nx
import pytest

from autoresearch.storage import StorageManager
from autoresearch.config.models import ConfigModel, StorageConfig
from autoresearch.config.loader import ConfigLoader


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
        cfg = ConfigLoader().config.storage
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS embeddings_hnsw ON embeddings USING hnsw (embedding) "
            f"WITH (m={cfg.hnsw_m}, ef_construction={cfg.hnsw_ef_construction}, metric='{cfg.hnsw_metric}')"
        )
        self._conn.execute(f"SET hnsw_ef_search={cfg.hnsw_ef_search}")

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
            hnsw_ef_search=20,
            hnsw_auto_tune=True,
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
    assert any(
        "m=8" in cmd and "ef_construction=100" in cmd and "metric='cosine'" in cmd
        for cmd in dummy.commands
    )
    assert any("SET hnsw_ef_search=20" in cmd for cmd in dummy.commands)


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

    with pytest.raises(StorageError) as excinfo:
        StorageManager.vector_search([0.0, 0.0], k=1)
    assert "Vector search failed" in str(excinfo.value)
    assert excinfo.value.__cause__ is not None


def test_refresh_vector_index(monkeypatch):
    backend = MagicMock()
    monkeypatch.setattr("autoresearch.storage._db_backend", backend, raising=False)
    monkeypatch.setattr(StorageManager, "_ensure_storage_initialized", lambda: None)

    StorageManager.refresh_vector_index()

    backend.refresh_hnsw_index.assert_called_once()


def test_embedding_update_triggers_index_refresh(monkeypatch):
    backend = MagicMock()
    graph = nx.DiGraph()
    store = MagicMock()
    monkeypatch.setattr("autoresearch.storage._db_backend", backend, raising=False)
    monkeypatch.setattr("autoresearch.storage._graph", graph, raising=False)
    monkeypatch.setattr("autoresearch.storage._rdf_store", store, raising=False)
    monkeypatch.setattr(StorageManager, "_enforce_ram_budget", lambda budget: None)
    monkeypatch.setattr(StorageManager, "_current_ram_mb", lambda: 0)
    monkeypatch.setattr(StorageManager, "has_vss", lambda: True)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: _mock_config())
    ConfigLoader()._config = None

    called = {"count": 0}

    def refresh():
        called["count"] += 1

    monkeypatch.setattr(StorageManager, "refresh_vector_index", refresh)

    StorageManager.persist_claim({"id": "c1", "type": "fact", "content": "c", "embedding": [0.1]})
    StorageManager.persist_claim({"id": "c1", "embedding": [0.2]}, partial_update=True)

    assert called["count"] == 2
