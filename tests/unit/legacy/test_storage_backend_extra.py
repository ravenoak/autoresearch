# mypy: ignore-errors
from unittest.mock import MagicMock, patch

import pytest

from autoresearch.errors import StorageError
from autoresearch.storage_backends import DuckDBStorageBackend


def test_connection_context_no_pool():
    backend = DuckDBStorageBackend()
    mock_conn = MagicMock()
    backend._conn = mock_conn
    backend._pool = None
    with backend.connection() as conn:
        assert conn is mock_conn


@patch("autoresearch.storage_backends.duckdb.connect")
def test_persist_claim_calls_execute(mock_connect):
    conn = MagicMock()
    mock_connect.return_value = conn
    backend = DuckDBStorageBackend()
    backend.setup(db_path=":memory:")
    conn.execute.reset_mock()
    claim = {
        "id": "c1",
        "type": "fact",
        "content": "text",
        "confidence": 0.5,
        "relations": [{"src": "c1", "dst": "c2", "rel": "r", "weight": 0.1}],
        "embedding": [0.0] * 384,
    }
    backend.persist_claim(claim)
    conn.execute.assert_any_call(
        "INSERT INTO nodes VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
        ["c1", "fact", "text", 0.5],
    )
    conn.execute.assert_any_call(
        "INSERT INTO edges VALUES (?, ?, ?, ?)",
        ["c1", "c2", "r", 0.1],
    )
    conn.execute.assert_any_call(
        "INSERT INTO embeddings VALUES (?, ?)",
        ["c1", claim["embedding"]],
    )


@patch("autoresearch.storage_backends.duckdb.connect")
def test_persist_claim_failure(mock_connect):
    conn = MagicMock()
    mock_connect.return_value = conn
    backend = DuckDBStorageBackend()
    backend.setup(db_path=":memory:")
    conn.execute.side_effect = Exception("fail")
    with pytest.raises(StorageError):
        backend.persist_claim({"id": "c1"})


@patch("autoresearch.storage_backends.duckdb.connect")
def test_vector_search_no_vss(mock_connect):
    conn = MagicMock()
    mock_connect.return_value = conn
    backend = DuckDBStorageBackend()
    backend.setup(db_path=":memory:")
    backend._has_vss = False
    with pytest.raises(StorageError):
        backend.vector_search([0.1, 0.2, 0.3])


@patch("autoresearch.storage_backends.duckdb.connect")
def test_vector_search_failure(mock_connect):
    conn = MagicMock()
    mock_connect.return_value = conn
    backend = DuckDBStorageBackend()
    backend.setup(db_path=":memory:")
    conn.execute.side_effect = Exception("boom")
    backend._has_vss = True
    with pytest.raises(StorageError):
        backend.vector_search([0.1, 0.2, 0.3])
