from unittest.mock import MagicMock
from autoresearch.storage_backends import DuckDBStorageBackend


def test_connection_context_no_pool():
    backend = DuckDBStorageBackend()
    mock_conn = MagicMock()
    backend._conn = mock_conn
    backend._pool = None
    with backend.connection() as conn:
        assert conn is mock_conn
