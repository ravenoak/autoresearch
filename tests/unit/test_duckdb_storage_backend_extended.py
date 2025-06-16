"""
Extended tests for the DuckDBStorageBackend class.

This module contains additional tests for the DuckDBStorageBackend class
to improve test coverage, focusing on methods that were not covered
in the original test_duckdb_storage_backend.py file.
"""

import os
import pytest
from unittest.mock import patch, MagicMock, call
import duckdb
import numpy as np

from autoresearch.storage_backends import DuckDBStorageBackend
from autoresearch.errors import StorageError, NotFoundError
from autoresearch.config import ConfigModel, StorageConfig


class TestDuckDBStorageBackendExtended:
    """Extended tests for the DuckDBStorageBackend class."""

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_create_hnsw_index(self, mock_connect):
        """Test creating an HNSW index."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Mock the ConfigLoader
        with patch("autoresearch.storage_backends.ConfigLoader") as mock_config_loader:
            mock_config = MagicMock()
            mock_config.config.storage.hnsw_m = 16
            mock_config.config.storage.hnsw_ef_construction = 64
            mock_config.config.storage.hnsw_metric = "euclidean"
            mock_config_loader.return_value = mock_config

            # Mock the VSSExtensionLoader
            with patch("autoresearch.extensions.VSSExtensionLoader.verify_extension", return_value=True):
                with patch("autoresearch.extensions.VSSExtensionLoader.load_extension", return_value=True):
                    # Setup the backend
                    backend = DuckDBStorageBackend()
                    backend._conn = mock_conn
                    backend._has_vss = True

                    # Create the HNSW index
                    backend.create_hnsw_index()

                    # Verify that the execute method was called with the correct query
                    mock_conn.execute.assert_any_call(
                        "CREATE INDEX IF NOT EXISTS embeddings_hnsw "
                        "ON embeddings USING hnsw (embedding) "
                        "WITH (m=16, ef_construction=64, metric='euclidean')"
                    )

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_create_hnsw_index_extension_not_loaded(self, mock_connect):
        """Test creating an HNSW index when the VSS extension is not loaded."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Mock the ConfigLoader
        with patch("autoresearch.storage_backends.ConfigLoader") as mock_config_loader:
            mock_config = MagicMock()
            mock_config.config.storage.hnsw_m = 16
            mock_config.config.storage.hnsw_ef_construction = 64
            mock_config.config.storage.hnsw_metric = "euclidean"
            mock_config_loader.return_value = mock_config

            # Mock the VSSExtensionLoader
            with patch("autoresearch.extensions.VSSExtensionLoader.verify_extension", return_value=False):
                with patch("autoresearch.extensions.VSSExtensionLoader.load_extension", return_value=False):
                    # Setup the backend
                    backend = DuckDBStorageBackend()
                    backend._conn = mock_conn
                    backend._has_vss = False

                    # Create the HNSW index
                    backend.create_hnsw_index()

                    # Verify that the execute method was called to check for the extension
                    mock_conn.execute.assert_any_call(
                        "CREATE INDEX IF NOT EXISTS embeddings_hnsw "
                        "ON embeddings USING hnsw (embedding) "
                        "WITH (m=16, ef_construction=64, metric='euclidean')"
                    )

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_create_hnsw_index_error(self, mock_connect):
        """Test error handling when creating an HNSW index."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Mock the ConfigLoader
        with patch("autoresearch.storage_backends.ConfigLoader") as mock_config_loader:
            mock_config = MagicMock()
            mock_config.config.storage.hnsw_m = 16
            mock_config.config.storage.hnsw_ef_construction = 64
            mock_config.config.storage.hnsw_metric = "euclidean"
            mock_config_loader.return_value = mock_config

            # Mock the VSSExtensionLoader
            with patch("autoresearch.extensions.VSSExtensionLoader.verify_extension", return_value=True):
                with patch("autoresearch.extensions.VSSExtensionLoader.load_extension", return_value=True):
                    # Setup the backend
                    backend = DuckDBStorageBackend()
                    backend._conn = mock_conn
                    backend._has_vss = True

                    # Mock the execute method to raise an exception
                    mock_conn.execute.side_effect = Exception("Failed to create index")

                    # Set the environment variable to strict mode
                    with patch.dict(os.environ, {"AUTORESEARCH_STRICT_EXTENSIONS": "true"}):
                        # Create the HNSW index and expect a StorageError
                        with pytest.raises(StorageError) as excinfo:
                            backend.create_hnsw_index()

                        # Verify that the error message is correct
                        assert "Failed to create HNSW index" in str(excinfo.value)

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_persist_claim(self, mock_connect):
        """Test persisting a claim."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Setup the backend
        backend = DuckDBStorageBackend()
        backend._conn = mock_conn

        # Persist a claim
        claim = {
            "id": "test_id",
            "type": "test_type",
            "content": "test_content",
            "confidence": 0.9,
            "relations": [
                {"src": "test_id", "dst": "other_id", "rel": "test_rel", "weight": 0.8}
            ],
            "embedding": [0.1, 0.2, 0.3]
        }
        backend.persist_claim(claim)

        # Verify that the execute method was called with the correct queries
        expected_calls = [
            call("INSERT INTO nodes VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                 ["test_id", "test_type", "test_content", 0.9]),
            call("INSERT INTO edges VALUES (?, ?, ?, ?)",
                 ["test_id", "other_id", "test_rel", 0.8]),
            call("INSERT INTO embeddings VALUES (?, ?)",
                 ["test_id", [0.1, 0.2, 0.3]]),
        ]
        mock_conn.execute.assert_has_calls(expected_calls, any_order=True)

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_persist_claim_minimal(self, mock_connect):
        """Test persisting a minimal claim with only an ID."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Setup the backend
        backend = DuckDBStorageBackend()
        backend._conn = mock_conn

        # Persist a minimal claim
        claim = {"id": "test_id"}
        backend.persist_claim(claim)

        # Verify that the execute method was called with the correct query
        mock_conn.execute.assert_called_once_with(
            "INSERT INTO nodes VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
            ["test_id", "", "", 0.0]
        )

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_persist_claim_error(self, mock_connect):
        """Test error handling when persisting a claim."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Setup the backend
        backend = DuckDBStorageBackend()
        backend._conn = mock_conn

        # Mock the execute method to raise an exception
        mock_conn.execute.side_effect = Exception("Failed to persist claim")

        # Persist a claim and expect a StorageError
        with pytest.raises(StorageError) as excinfo:
            backend.persist_claim({"id": "test_id"})

        # Verify that the error message is correct
        assert "Failed to persist claim to DuckDB" in str(excinfo.value)

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_vector_search(self, mock_connect):
        """Test vector search."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Mock the ConfigLoader
        with patch("autoresearch.storage_backends.ConfigLoader") as mock_config_loader:
            mock_config = MagicMock()
            mock_config.config.vector_nprobe = 10
            mock_config_loader.return_value = mock_config

            # Mock the fetchall method to return search results
            mock_result = MagicMock()
            mock_result.fetchall.return_value = [
                ["node1", [0.1, 0.2, 0.3]],
                ["node2", [0.4, 0.5, 0.6]]
            ]
            mock_conn.execute.return_value = mock_result

            # Setup the backend
            backend = DuckDBStorageBackend()
            backend._conn = mock_conn
            backend._has_vss = True

            # Perform a vector search
            results = backend.vector_search([0.1, 0.2, 0.3], k=2)

            # Verify that the execute method was called with the correct queries
            mock_conn.execute.assert_any_call("SET hnsw_ef_search=10")
            mock_conn.execute.assert_any_call(
                "SELECT node_id, embedding FROM embeddings "
                "ORDER BY embedding <-> [0.1, 0.2, 0.3] LIMIT 2"
            )

            # Verify that the results are correct
            assert len(results) == 2
            assert results[0]["node_id"] == "node1"
            assert results[0]["embedding"] == [0.1, 0.2, 0.3]
            assert results[1]["node_id"] == "node2"
            assert results[1]["embedding"] == [0.4, 0.5, 0.6]

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_vector_search_vss_not_available(self, mock_connect):
        """Test vector search when VSS is not available."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Setup the backend
        backend = DuckDBStorageBackend()
        backend._conn = mock_conn
        backend._has_vss = False

        # Perform a vector search and expect a StorageError
        with pytest.raises(StorageError) as excinfo:
            backend.vector_search([0.1, 0.2, 0.3])

        # Verify that the error message is correct
        assert "Vector search not available: VSS extension not loaded" in str(excinfo.value)

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_vector_search_error(self, mock_connect):
        """Test error handling during vector search."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Mock the ConfigLoader
        with patch("autoresearch.storage_backends.ConfigLoader") as mock_config_loader:
            mock_config = MagicMock()
            mock_config.config.vector_nprobe = 10
            mock_config_loader.return_value = mock_config

            # Mock the execute method to raise an exception
            mock_conn.execute.side_effect = Exception("Failed to perform vector search")

            # Setup the backend
            backend = DuckDBStorageBackend()
            backend._conn = mock_conn
            backend._has_vss = True

            # Perform a vector search and expect a StorageError
            with pytest.raises(StorageError) as excinfo:
                backend.vector_search([0.1, 0.2, 0.3])

            # Verify that the error message is correct
            assert "Vector search failed" in str(excinfo.value)

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_get_connection(self, mock_connect):
        """Test getting the DuckDB connection."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Setup the backend
        backend = DuckDBStorageBackend()
        backend._conn = mock_conn

        # Get the connection
        conn = backend.get_connection()

        # Verify that the connection is correct
        assert conn == mock_conn

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_get_connection_not_initialized(self, mock_connect):
        """Test getting the DuckDB connection when it's not initialized."""
        # Setup the backend
        backend = DuckDBStorageBackend()
        backend._conn = None

        # Get the connection and expect a NotFoundError
        with pytest.raises(NotFoundError) as excinfo:
            backend.get_connection()

        # Verify that the error message is correct
        assert "DuckDB connection not initialized" in str(excinfo.value)
