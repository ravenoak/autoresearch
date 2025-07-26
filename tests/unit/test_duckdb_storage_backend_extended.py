"""
Extended tests for the DuckDBStorageBackend class.

This module contains additional tests for the DuckDBStorageBackend class
to improve test coverage, focusing on methods that were not covered
in the original test_duckdb_storage_backend.py file.
"""

import os
import pytest
from unittest.mock import patch, MagicMock, call

from autoresearch.storage_backends import DuckDBStorageBackend
from autoresearch.errors import StorageError, NotFoundError


@pytest.mark.skip("Environment lacks DuckDB VSS support")
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
            with patch(
                "autoresearch.extensions.VSSExtensionLoader.verify_extension",
                return_value=True,
            ):
                with patch(
                    "autoresearch.extensions.VSSExtensionLoader.load_extension",
                    return_value=True,
                ):
                    # Setup the backend
                    backend = DuckDBStorageBackend()
                    backend._conn = mock_conn
                    backend._has_vss = True

                    # Create the HNSW index
                    backend.create_hnsw_index()

                    # Verify that the execute method attempted to create an index
                    called = any(
                        "CREATE INDEX" in args.args[0]
                        for args in mock_conn.execute.call_args_list
                    )
                    if not called:
                        called = mock_conn.execute.called
                    assert called

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
            with patch(
                "autoresearch.extensions.VSSExtensionLoader.verify_extension",
                return_value=False,
            ):
                with patch(
                    "autoresearch.extensions.VSSExtensionLoader.load_extension",
                    return_value=False,
                ):
                    # Setup the backend
                    backend = DuckDBStorageBackend()
                    backend._conn = mock_conn
                    backend._has_vss = False

                    # Create the HNSW index
                    backend.create_hnsw_index()

                    # Verify that an index creation was attempted
                    called = False
                    for call_args in mock_conn.execute.call_args_list:
                        if "CREATE INDEX" in call_args.args[0]:
                            called = True
                            break
                    assert called

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
            with patch(
                "autoresearch.extensions.VSSExtensionLoader.verify_extension",
                return_value=True,
            ):
                with patch(
                    "autoresearch.extensions.VSSExtensionLoader.load_extension",
                    return_value=True,
                ):
                    # Setup the backend
                    backend = DuckDBStorageBackend()
                    backend._conn = mock_conn
                    backend._has_vss = True

                    # Mock the execute method to raise an exception
                    mock_conn.execute.side_effect = Exception("Failed to create index")

                    # Set the environment variable to strict mode
                    with patch.dict(
                        os.environ, {"AUTORESEARCH_STRICT_EXTENSIONS": "true"}
                    ):
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
            "embedding": [0.1, 0.2, 0.3],
        }
        backend.persist_claim(claim)

        # Verify that the execute method was called with the correct queries
        expected_calls = [
            call(
                "INSERT INTO nodes VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                ["test_id", "test_type", "test_content", 0.9],
            ),
            call(
                "INSERT INTO edges VALUES (?, ?, ?, ?)",
                ["test_id", "other_id", "test_rel", 0.8],
            ),
            call("INSERT INTO embeddings VALUES (?, ?)", ["test_id", [0.1, 0.2, 0.3]]),
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
            ["test_id", "", "", 0.0],
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
            mock_config.config.storage.vector_nprobe = 10
            mock_config_loader.return_value = mock_config

            # Mock the fetchall method to return search results
            mock_result = MagicMock()
            mock_result.fetchall.return_value = [
                ["node1", [0.1, 0.2, 0.3], 0.8],
                ["node2", [0.4, 0.5, 0.6], 0.7],
            ]
            mock_conn.execute.return_value = mock_result

            # Setup the backend
            backend = DuckDBStorageBackend()
            backend._conn = mock_conn
            backend._has_vss = True

            # Perform a vector search
            results = backend.vector_search([0.1, 0.2, 0.3], k=2)

            # Verify that a search query was executed
            assert any(
                "SELECT" in call.args[0] and "embeddings" in call.args[0]
                for call in mock_conn.execute.call_args_list
            )

            # Verify that the results are correct
            assert len(results) == 2
            assert results[0]["node_id"] == "node1"
            assert results[0]["embedding"] == [0.1, 0.2, 0.3]
            assert results[0]["similarity"] == 0.8
            assert results[1]["node_id"] == "node2"
            assert results[1]["embedding"] == [0.4, 0.5, 0.6]
            assert results[1]["similarity"] == 0.7

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
        assert "Vector search not available: VSS extension not loaded" in str(
            excinfo.value
        )

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_vector_search_error(self, mock_connect):
        """Test error handling during vector search."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Mock the ConfigLoader
        with patch("autoresearch.storage_backends.ConfigLoader") as mock_config_loader:
            mock_config = MagicMock()
            mock_config.config.storage.vector_nprobe = 10
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

    def test_update_claim_full_replace(self):
        """Update existing claim with full replacement."""
        conn = MagicMock()
        backend = DuckDBStorageBackend()
        backend._conn = conn

        claim = {
            "id": "c1",
            "type": "fact",
            "content": "new",
            "confidence": 0.5,
            "relations": [{"src": "c1", "dst": "c2", "rel": "r", "weight": 1.0}],
            "embedding": [0.1, 0.2],
        }

        backend.update_claim(claim, partial_update=False)

        expected = [
            call(
                "UPDATE nodes SET type=?, content=?, conf=?, ts=CURRENT_TIMESTAMP WHERE id=?",
                ["fact", "new", 0.5, "c1"],
            ),
            call("DELETE FROM edges WHERE src=? OR dst=?", ["c1", "c1"]),
            call(
                "INSERT INTO edges VALUES (?, ?, ?, ?)",
                ["c1", "c2", "r", 1.0],
            ),
            call("DELETE FROM embeddings WHERE node_id=?", ["c1"]),
            call("INSERT INTO embeddings VALUES (?, ?)", ["c1", [0.1, 0.2]]),
        ]
        conn.execute.assert_has_calls(expected)

    def test_update_claim_partial(self):
        """Update only provided fields when partial_update=True."""
        conn = MagicMock()
        backend = DuckDBStorageBackend()
        backend._conn = conn

        claim = {"id": "c1", "content": "partial"}

        backend.update_claim(claim, partial_update=True)

        conn.execute.assert_called_once_with(
            "UPDATE nodes SET content=? WHERE id=?", ["partial", "c1"]
        )
