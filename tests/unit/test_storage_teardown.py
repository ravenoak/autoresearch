"""Tests for the teardown function in the storage module.

This module contains tests for the teardown function, which is responsible
for cleaning up storage resources.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from autoresearch.storage import StorageManager, teardown


def test_teardown_closes_resources():
    """Test that teardown closes all resources properly."""
    # Setup
    mock_backend = MagicMock()
    mock_graph = MagicMock()
    mock_rdf = MagicMock()
    mock_lru = MagicMock()

    with patch.object(StorageManager.context, "db_backend", mock_backend):
        with patch.object(StorageManager.context, "graph", mock_graph):
            with patch.object(StorageManager.context, "rdf_store", mock_rdf):
                with patch.object(StorageManager.state, "lru", mock_lru):
                    # Execute
                    teardown(context=StorageManager.context)

                    # Verify
                    mock_backend.close.assert_called_once()

                    # Check that the context variables are set to None
                    assert StorageManager.context.db_backend is None
                    assert StorageManager.context.graph is None
                    assert StorageManager.context.rdf_store is None


def test_teardown_removes_db_file():
    """Test that teardown removes the database file when remove_db is True."""
    # Setup
    mock_backend = MagicMock()
    mock_path = Path("test.db")

    # Create a temporary file to simulate the database
    with open(mock_path, "w") as f:
        f.write("test")

    assert mock_path.exists()

    # Set the _path attribute on the mock backend
    mock_backend._path = str(mock_path)

    with patch.object(StorageManager.context, "db_backend", mock_backend):
        # Execute
        teardown(remove_db=True, context=StorageManager.context)

        # Verify
        mock_backend.close.assert_called_once()
        assert not mock_path.exists()

    # Clean up in case the test fails
    if mock_path.exists():
        mock_path.unlink()


def test_teardown_handles_none_resources():
    """Test that teardown handles None resources gracefully."""
    # Setup
    with patch.object(StorageManager.context, "db_backend", None):
        with patch.object(StorageManager.context, "graph", None):
            with patch.object(StorageManager.context, "rdf_store", None):
                with patch.object(StorageManager.state, "lru", None):
                    # Execute
                    teardown(context=StorageManager.context)

                    # No assertions needed - the test passes if no exceptions are raised


def test_teardown_handles_close_error():
    """Test that teardown handles errors when closing resources."""
    # Setup
    mock_backend = MagicMock()
    mock_backend.close.side_effect = Exception("Close error")

    with patch.object(StorageManager.context, "db_backend", mock_backend):
        # Execute
        teardown(context=StorageManager.context)

        # Verify
        mock_backend.close.assert_called_once()
        # No assertions needed for the exception - the test passes if teardown completes
