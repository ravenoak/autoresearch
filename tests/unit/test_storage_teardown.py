"""Tests for the teardown function in the storage module.

This module contains tests for the teardown function, which is responsible
for cleaning up storage resources.
"""

from unittest.mock import patch, MagicMock
from pathlib import Path

from autoresearch.storage import teardown


def test_teardown_closes_resources():
    """Test that teardown closes all resources properly."""
    # Setup
    mock_backend = MagicMock()
    mock_graph = MagicMock()
    mock_rdf = MagicMock()
    mock_lru = MagicMock()

    with patch("autoresearch.storage._db_backend", mock_backend):
        with patch("autoresearch.storage._graph", mock_graph):
            with patch("autoresearch.storage._rdf_store", mock_rdf):
                with patch("autoresearch.storage._lru", mock_lru):
                    # Execute
                    teardown()

                    # Verify
                    mock_backend.close.assert_called_once()

                    # Check that the global variables are set to None
                    # We need to import them again to get the current values
                    from autoresearch.storage import _db_backend, _graph, _rdf_store

                    assert _db_backend is None
                    assert _graph is None
                    assert _rdf_store is None


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

    with patch("autoresearch.storage._db_backend", mock_backend):
        # Execute
        teardown(remove_db=True)

        # Verify
        mock_backend.close.assert_called_once()
        assert not mock_path.exists()

    # Clean up in case the test fails
    if mock_path.exists():
        mock_path.unlink()


def test_teardown_handles_none_resources():
    """Test that teardown handles None resources gracefully."""
    # Setup
    with patch("autoresearch.storage._db_backend", None):
        with patch("autoresearch.storage._graph", None):
            with patch("autoresearch.storage._rdf_store", None):
                with patch("autoresearch.storage._lru", None):
                    # Execute
                    teardown()

                    # No assertions needed - the test passes if no exceptions are raised


def test_teardown_handles_close_error():
    """Test that teardown handles errors when closing resources."""
    # Setup
    mock_backend = MagicMock()
    mock_backend.close.side_effect = Exception("Close error")

    with patch("autoresearch.storage._db_backend", mock_backend):
        # Execute
        teardown()

        # Verify
        mock_backend.close.assert_called_once()
        # No assertions needed for the exception - the test passes if teardown completes
