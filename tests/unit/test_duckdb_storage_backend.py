import pytest
from unittest.mock import patch, MagicMock, call

import duckdb

from autoresearch.storage_backends import DuckDBStorageBackend
from autoresearch.errors import StorageError
from autoresearch.config.loader import ConfigLoader


@pytest.fixture(autouse=True)
def reset_config_loader():
    """Reset ``ConfigLoader`` before and after each test."""
    ConfigLoader.reset_instance()
    with patch("autoresearch.storage_backends.ConfigLoader") as mock_loader:
        mock_cfg = MagicMock()
        mock_cfg.storage.duckdb.path = "kg.duckdb"
        mock_cfg.storage.vector_extension = False
        mock_loader.return_value.config = mock_cfg
        yield
    ConfigLoader.reset_instance()


class TestDuckDBStorageBackend:
    """Test the DuckDBStorageBackend class."""

    def test_init(self):
        """Test initialization of the DuckDBStorageBackend."""
        backend = DuckDBStorageBackend()
        assert backend._conn is None
        assert backend._path is None
        assert backend._lock is not None
        assert backend._has_vss is False

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_setup_with_default_path(self, mock_connect):
        """Test setup with default path."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Mock the ConfigLoader
        with patch("autoresearch.storage_backends.ConfigLoader") as mock_config_loader:
            mock_config = MagicMock()
            # Create nested structure for duckdb config
            mock_config.config.storage.duckdb = MagicMock()
            mock_config.config.storage.duckdb.path = ":memory:"
            mock_config_loader.return_value = mock_config

            # Mock the _create_tables method
            with patch.object(
                DuckDBStorageBackend, "_create_tables"
            ) as mock_create_tables:
                # Setup the backend
                backend = DuckDBStorageBackend()
                backend.setup()

                # Verify that the connection was created with the correct path
                mock_connect.assert_called_once_with(":memory:")

                # Verify that the tables were created
                mock_create_tables.assert_called_once()

                # Verify that the connection is set
                assert backend._conn is not None
                assert backend._path == ":memory:"

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_setup_with_custom_path(self, mock_connect):
        """Test setup with custom path."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Mock the ConfigLoader similar to the default path test
        with patch("autoresearch.storage_backends.ConfigLoader") as mock_loader:
            mock_config = MagicMock()
            mock_config.config.storage.duckdb = MagicMock()
            mock_config.config.storage.duckdb.path = ":memory:"
            mock_loader.return_value = mock_config

            # Mock the _create_tables method
            with patch.object(DuckDBStorageBackend, "_create_tables") as mock_create_tables:
                # Setup the backend with a custom path
                backend = DuckDBStorageBackend()
                backend.setup(db_path="/path/to/db.duckdb")

            # Verify that the connection was created with the correct path
            mock_connect.assert_called_once_with("/path/to/db.duckdb")

            # Verify that the tables were created
            mock_create_tables.assert_called_once()

            # Verify that the connection is set
            assert backend._conn is not None
            assert backend._path == "/path/to/db.duckdb"

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_setup_with_connection_error(self, mock_connect):
        """Test setup with connection error."""
        # Mock the connection to raise an exception
        mock_connect.side_effect = Exception("Connection error")

        # Setup the backend and expect a StorageError
        backend = DuckDBStorageBackend()
        with pytest.raises(StorageError) as excinfo:
            backend.setup(db_path=":memory:")

        # Verify that the error message is correct
        assert "Failed to connect to DuckDB database" in str(excinfo.value)

        # Verify that the connection is None
        assert backend._conn is None

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_setup_table_creation_failure(self, mock_connect):
        """Errors during table creation raise ``StorageError``."""

        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("boom")
        mock_connect.return_value = mock_conn

        backend = DuckDBStorageBackend()
        with pytest.raises(StorageError):
            backend.setup(db_path=":memory:")

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_create_tables(self, mock_connect):
        """Test creating tables."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Setup the backend
        backend = DuckDBStorageBackend()
        backend.setup(db_path=":memory:")

        # Verify that the execute method was called for each table creation
        expected_calls = [
            call(
                "CREATE TABLE IF NOT EXISTS nodes(id VARCHAR, type VARCHAR, content VARCHAR, conf DOUBLE, ts TIMESTAMP)"
            ),
            call(
                "CREATE TABLE IF NOT EXISTS edges(src VARCHAR, dst VARCHAR, rel VARCHAR, w DOUBLE)"
            ),
            call(
                "CREATE TABLE IF NOT EXISTS embeddings(node_id VARCHAR, embedding FLOAT[384])"
            ),
            call("CREATE TABLE IF NOT EXISTS metadata(key VARCHAR, value VARCHAR)"),
        ]
        mock_conn.execute.assert_has_calls(expected_calls, any_order=True)

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_initialize_schema_version(self, mock_connect):
        """Test initializing schema version."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Mock the fetchall method to return an empty list (no version)
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_conn.execute.return_value = mock_result

        # Setup the backend
        backend = DuckDBStorageBackend()
        backend.setup(
            db_path=":memory:", skip_migrations=True
        )  # Skip migrations to isolate the test

        # Call the _initialize_schema_version method directly
        backend._initialize_schema_version()

        # Verify that the execute method was called to insert the schema version
        mock_conn.execute.assert_any_call(
            "INSERT INTO metadata (key, value) VALUES ('schema_version', '1')"
        )

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_get_schema_version(self, mock_connect):
        """Test getting schema version."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Mock the fetchall method to return a schema version
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [["2"]]
        mock_conn.execute.return_value = mock_result

        # Setup the backend
        backend = DuckDBStorageBackend()
        backend.setup(db_path=":memory:")

        # Get the schema version
        version = backend.get_schema_version()

        # Verify that the execute method was called with the correct query
        mock_conn.execute.assert_any_call(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        )

        # Verify that the schema version is correct
        assert version == 2

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_get_schema_version_no_version(self, mock_connect):
        """Test getting schema version when no version exists."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Mock the fetchall method to return an empty list (no version)
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_conn.execute.return_value = mock_result

        # Setup the backend
        backend = DuckDBStorageBackend()
        backend.setup(db_path=":memory:", skip_migrations=True)

        # Get the schema version with initialize_if_missing=False
        version = backend.get_schema_version(initialize_if_missing=False)

        # Verify that the execute method was called with the correct query
        mock_conn.execute.assert_any_call(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        )

        # Verify that the schema version is None
        assert version is None

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_update_schema_version(self, mock_connect):
        """Test updating schema version."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Setup the backend
        backend = DuckDBStorageBackend()
        backend.setup(db_path=":memory:")

        # Update the schema version
        backend.update_schema_version(3)

        # Verify that the execute method was called with the correct query and parameters
        mock_conn.execute.assert_any_call(
            "UPDATE metadata SET value = ? WHERE key = 'schema_version'", ["3"]
        )

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_run_migrations(self, mock_connect):
        """Test running migrations."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Mock the get_schema_version method to return version 1
        with patch.object(DuckDBStorageBackend, "get_schema_version", return_value=1):
            # Mock the update_schema_version method
            with patch.object(
                DuckDBStorageBackend, "update_schema_version"
            ) as mock_update_version:
                # Setup the backend
                backend = DuckDBStorageBackend()
                backend.setup(db_path=":memory:")

                # Call the _run_migrations method directly
                backend._run_migrations()

                # Verify that the update_schema_version method was not called (no migrations needed)
                mock_update_version.assert_not_called()

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_has_vss_true(self, mock_connect):
        """Test has_vss method when VSS is available."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Mock the execute method to not raise an exception
        mock_conn.execute.return_value = MagicMock()

        backend = DuckDBStorageBackend()
        with patch(
            "autoresearch.storage_backends.ConfigLoader",
            **{"return_value.config.storage.vector_extension": True,
               "return_value.config.storage.duckdb.path": ":memory:"},
        ):
            with patch(
                "autoresearch.extensions.VSSExtensionLoader.load_extension",
                return_value=True,
            ):
                backend.setup(db_path=":memory:")

        # Check if VSS is available
        has_vss = backend.has_vss()

        # Verify that has_vss returns True
        assert has_vss is True

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_has_vss_false(self, mock_connect):
        """Test has_vss method when VSS is not available."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Create a side effect function that raises a DuckDB error only for VSS-related calls
        def side_effect(query, *args, **kwargs):
            if (
                "duckdb_extensions()" in query
                and "extension_name = 'vss'" in query
                or "INSTALL vss" in query
                or "LOAD vss" in query
            ):
                raise duckdb.Error("VSS not available")
            mock_result = MagicMock()
            mock_result.fetchone.return_value = ["1"]  # For schema version query
            return mock_result

        # Set the side effect
        mock_conn.execute.side_effect = side_effect

        # Setup the backend with skip_migrations=True to avoid calling _run_migrations
        backend = DuckDBStorageBackend()

        # Patch the VSSExtensionLoader.verify_extension method to return False
        with patch(
            "autoresearch.extensions.VSSExtensionLoader.verify_extension",
            return_value=False,
        ):
            # Patch the VSSExtensionLoader.load_extension method to return False
            with patch(
                "autoresearch.extensions.VSSExtensionLoader.load_extension",
                return_value=False,
            ):
                # Setup the backend
                backend.setup(db_path=":memory:", skip_migrations=True)

                # Check if VSS is available
                has_vss = backend.has_vss()

                # Verify that has_vss returns False
                assert has_vss is False

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_close(self, mock_connect):
        """Test closing the connection."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Setup the backend
        backend = DuckDBStorageBackend()
        backend.setup(db_path=":memory:")

        # Close the connection
        backend.close()

        # Verify that the close method was called
        mock_conn.close.assert_called_once()

        # Verify that the connection is None
        assert backend._conn is None

        # Verify that the path is None
        assert backend._path is None

    @patch("autoresearch.storage_backends.duckdb.connect")
    def test_clear(self, mock_connect):
        """Test clearing the database."""
        # Mock the connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Setup the backend
        backend = DuckDBStorageBackend()
        backend.setup(db_path=":memory:")

        # Clear the database
        backend.clear()

        # Verify that the execute method was called for each table
        expected_calls = [
            call("DELETE FROM nodes"),
            call("DELETE FROM edges"),
            call("DELETE FROM embeddings"),
        ]
        mock_conn.execute.assert_has_calls(expected_calls, any_order=True)
