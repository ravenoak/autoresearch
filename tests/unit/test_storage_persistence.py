import pytest
from unittest.mock import patch, MagicMock

from autoresearch.storage import StorageManager
from autoresearch.errors import StorageError


def test_ensure_storage_initialized_success():
    """Test that _ensure_storage_initialized succeeds when storage is initialized."""
    # Mock the global variables
    with patch.object(StorageManager.context, "db_backend", MagicMock()):
        with patch.object(StorageManager.context, "graph", MagicMock()):
            with patch.object(StorageManager.context, "rdf_store", MagicMock()):
                # Should not raise an exception
                StorageManager._ensure_storage_initialized()


def test_ensure_storage_initialized_calls_setup():
    """Test that _ensure_storage_initialized calls setup when storage is not initialized."""
    # Mock the global variables to be None
    with patch.object(StorageManager.context, "db_backend", None):
        with patch.object(StorageManager.context, "graph", None):
            with patch.object(StorageManager.context, "rdf_store", None):
                with patch("autoresearch.storage.setup") as mock_setup:
                    # Mock the setup function to set the global variables
                    def mock_setup_impl():
                        import autoresearch.storage as storage

                        storage.StorageManager.context.db_backend = MagicMock()
                        storage.StorageManager.context.graph = MagicMock()
                        storage.StorageManager.context.rdf_store = MagicMock()

                    mock_setup.side_effect = mock_setup_impl

                    # Should call setup
                    StorageManager._ensure_storage_initialized()

                    # Verify setup was called
                    mock_setup.assert_called_once()


def test_ensure_storage_initialized_setup_fails():
    """Test that _ensure_storage_initialized raises StorageError when setup fails."""
    # Mock the global variables to be None
    with patch.object(StorageManager.context, "db_backend", None):
        with patch.object(StorageManager.context, "graph", None):
            with patch.object(StorageManager.context, "rdf_store", None):
                with patch(
                    "autoresearch.storage.setup", side_effect=Exception("Setup failed")
                ):
                    # Should raise StorageError
                    with pytest.raises(StorageError) as excinfo:
                        StorageManager._ensure_storage_initialized()

                    assert "Failed to initialize storage components" in str(
                        excinfo.value
                    )
                    assert excinfo.value.__cause__ is not None


def test_ensure_storage_initialized_db_still_none():
    """Test that _ensure_storage_initialized raises StorageError when db_backend is still None after setup."""
    # Mock the global variables
    with patch.object(StorageManager.context, "db_backend", None):
        with patch.object(StorageManager.context, "graph", MagicMock()):
            with patch.object(StorageManager.context, "rdf_store", MagicMock()):
                with patch("autoresearch.storage.setup"):
                    # Should raise StorageError
                    with pytest.raises(StorageError) as excinfo:
                        StorageManager._ensure_storage_initialized()

                    assert "DuckDB backend not initialized" in str(excinfo.value)


def test_ensure_storage_initialized_graph_still_none():
    """Test that _ensure_storage_initialized raises StorageError when graph is still None after setup."""
    # Mock the global variables
    with patch.object(StorageManager.context, "db_backend", MagicMock()):
        with patch.object(StorageManager.context, "graph", None):
            with patch.object(StorageManager.context, "rdf_store", MagicMock()):
                with patch("autoresearch.storage.setup"):
                    # Should raise StorageError
                    with pytest.raises(StorageError) as excinfo:
                        StorageManager._ensure_storage_initialized()

                    assert "Graph not initialized" in str(excinfo.value)


def test_ensure_storage_initialized_rdf_still_none():
    """Test that _ensure_storage_initialized raises StorageError when rdf_store is still None after setup."""
    # Mock the global variables
    with patch.object(StorageManager.context, "db_backend", MagicMock()):
        with patch.object(StorageManager.context, "graph", MagicMock()):
            with patch.object(StorageManager.context, "rdf_store", None):
                with patch("autoresearch.storage.setup"):
                    # Should raise StorageError
                    with pytest.raises(StorageError) as excinfo:
                        StorageManager._ensure_storage_initialized()

                    assert "RDF store not initialized" in str(excinfo.value)


def test_persist_to_networkx():
    """Test that _persist_to_networkx correctly persists a claim to NetworkX."""
    # Create a mock graph
    mock_graph = MagicMock()
    mock_lru = {}

    # Create a test claim
    claim = {
        "id": "test-id",
        "type": "fact",
        "content": "test content",
        "confidence": 0.9,
        "attributes": {"verified": True},
        "relations": [
            {
                "src": "test-id",
                "dst": "source-1",
                "rel": "cites",
                "weight": 1.0,
                "attributes": {"quality": "high"},
            }
        ],
    }

    with patch.object(StorageManager.context, "graph", mock_graph):
        with patch("autoresearch.storage._lru", mock_lru):
            # Call the method
            StorageManager._persist_to_networkx(claim)

            # Verify the graph was updated correctly
            mock_graph.add_node.assert_called_once_with(
                "test-id", verified=True, confidence=0.9
            )

            mock_graph.add_edge.assert_called_once_with(
                "test-id", "source-1", quality="high"
            )

            # Verify the LRU cache was updated
            assert "test-id" in mock_lru


def test_persist_to_duckdb():
    """Test that _persist_to_duckdb correctly persists a claim to DuckDB."""
    # Create a mock DuckDB backend
    mock_db_backend = MagicMock()

    # Create a test claim
    claim = {
        "id": "test-id",
        "type": "fact",
        "content": "test content",
        "confidence": 0.9,
        "relations": [
            {"src": "test-id", "dst": "source-1", "rel": "cites", "weight": 1.0}
        ],
        "embedding": [0.1, 0.2, 0.3],
    }

    with patch.object(StorageManager.context, "db_backend", mock_db_backend):
        # Call the method
        StorageManager._persist_to_duckdb(claim)

        # Verify the backend was used correctly
        mock_db_backend.persist_claim.assert_called_once_with(claim)


def test_persist_to_rdf():
    """Test that _persist_to_rdf correctly persists a claim to RDF."""
    # Create a mock RDF store
    mock_rdf_store = MagicMock()

    # Create a test claim
    claim = {"id": "test-id", "attributes": {"verified": True, "source": "test-source"}}

    with patch.object(StorageManager.context, "rdf_store", mock_rdf_store):
        with patch("rdflib.URIRef") as mock_uri_ref:
            with patch("rdflib.Literal") as mock_literal:
                # Set up the mocks
                mock_uri_ref.side_effect = lambda x: x
                mock_literal.side_effect = lambda x: x

                # Call the method
                StorageManager._persist_to_rdf(claim)

                # Verify the RDF store was updated correctly
                assert mock_rdf_store.add.call_count == 2

                # Check attribute triples
                mock_rdf_store.add.assert_any_call(
                    ("urn:claim:test-id", "urn:prop:verified", True)
                )
                mock_rdf_store.add.assert_any_call(
                    ("urn:claim:test-id", "urn:prop:source", "test-source")
                )
