import os
import pytest
from unittest.mock import patch, MagicMock

from autoresearch.extensions import VSSExtensionLoader
from autoresearch.errors import StorageError


class TestVSSExtensionLoader:
    """Test the VSSExtensionLoader class."""

    def test_verify_extension_success(self):
        """Test that verify_extension returns True when the extension is loaded."""
        # Create a mock connection that successfully executes the verification query
        conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [("vss", "loaded")]
        conn.execute.return_value = mock_result

        # Verify that the extension is reported as loaded
        assert VSSExtensionLoader.verify_extension(conn) is True
        conn.execute.assert_called_once_with(
            "SELECT * FROM duckdb_extensions() WHERE extension_name = 'vss'"
        )

    def test_verify_extension_failure(self):
        """Test that verify_extension returns False when the extension is not loaded."""
        # Create a mock connection that raises an exception when executing the verification query
        conn = MagicMock()
        conn.execute.side_effect = Exception("Extension not loaded")

        # Verify that the extension is reported as not loaded
        assert VSSExtensionLoader.verify_extension(conn) is False
        conn.execute.assert_called_once_with(
            "SELECT * FROM duckdb_extensions() WHERE extension_name = 'vss'"
        )

    @patch("autoresearch.extensions.ConfigLoader")
    def test_load_extension_from_filesystem_success(self, mock_config_loader):
        """Test loading the extension from the filesystem."""
        # Configure the mock config loader
        mock_config = MagicMock()
        mock_config.config.storage.vector_extension_path = (
            "/path/to/vss.duckdb_extension"
        )
        mock_config_loader.return_value = mock_config

        # Create a mock connection
        conn = MagicMock()

        # Mock os.path.exists to return True
        with patch("os.path.exists", return_value=True):
            # Mock verify_extension to return True
            with patch.object(
                VSSExtensionLoader, "verify_extension", return_value=True
            ):
                # Load the extension
                result = VSSExtensionLoader.load_extension(conn)

                # Verify that the extension was loaded
                assert result is True
                conn.execute.assert_called_once_with(
                    "LOAD '/path/to/vss.duckdb_extension'"
                )

    @patch("autoresearch.extensions.ConfigLoader")
    def test_load_extension_from_filesystem_invalid_path(self, mock_config_loader):
        """Test loading the extension from an invalid filesystem path."""
        # Configure the mock config loader
        mock_config = MagicMock()
        mock_config.config.storage.vector_extension_path = "/path/to/vss.invalid"
        mock_config_loader.return_value = mock_config

        # Create a mock connection
        conn = MagicMock()

        # Mock the download and install to succeed
        with patch.object(VSSExtensionLoader, "verify_extension", return_value=True):
            # Load the extension
            result = VSSExtensionLoader.load_extension(conn)

            # Verify that the extension was loaded via download
            assert result is True
            conn.execute.assert_any_call("INSTALL vss")
            conn.execute.assert_any_call("LOAD vss")

    @patch("autoresearch.extensions.ConfigLoader")
    def test_load_extension_from_filesystem_file_not_found(self, mock_config_loader):
        """Test loading the extension from a non-existent filesystem path."""
        # Configure the mock config loader
        mock_config = MagicMock()
        mock_config.config.storage.vector_extension_path = (
            "/path/to/vss.duckdb_extension"
        )
        mock_config_loader.return_value = mock_config

        # Create a mock connection
        conn = MagicMock()

        # Mock os.path.exists to return False
        with patch("os.path.exists", return_value=False):
            # Mock the download and install to succeed
            with patch.object(
                VSSExtensionLoader, "verify_extension", return_value=True
            ):
                # Load the extension
                result = VSSExtensionLoader.load_extension(conn)

                # Verify that the extension was loaded via download
                assert result is True
                conn.execute.assert_any_call("INSTALL vss")
                conn.execute.assert_any_call("LOAD vss")

    @patch("autoresearch.extensions.ConfigLoader")
    def test_load_extension_from_filesystem_verification_failure(
        self, mock_config_loader
    ):
        """Test loading the extension from the filesystem but verification fails."""
        # Configure the mock config loader
        mock_config = MagicMock()
        mock_config.config.storage.vector_extension_path = (
            "/path/to/vss.duckdb_extension"
        )
        mock_config_loader.return_value = mock_config

        # Create a mock connection
        conn = MagicMock()

        # Mock os.path.exists to return True
        with patch("os.path.exists", return_value=True):
            # Mock verify_extension to return False for filesystem but True for download
            with patch.object(
                VSSExtensionLoader, "verify_extension", side_effect=[False, True]
            ):
                # Load the extension
                result = VSSExtensionLoader.load_extension(conn)

                # Verify that the extension was loaded via download
                assert result is True
                conn.execute.assert_any_call("LOAD '/path/to/vss.duckdb_extension'")
                conn.execute.assert_any_call("INSTALL vss")
                conn.execute.assert_any_call("LOAD vss")

    @patch("autoresearch.extensions.ConfigLoader")
    def test_load_extension_download_success(self, mock_config_loader):
        """Test downloading and installing the extension."""
        # Configure the mock config loader
        mock_config = MagicMock()
        mock_config.config.storage.vector_extension_path = None
        mock_config_loader.return_value = mock_config

        # Create a mock connection
        conn = MagicMock()

        # Mock verify_extension to return True
        with patch.object(VSSExtensionLoader, "verify_extension", return_value=True):
            # Load the extension
            result = VSSExtensionLoader.load_extension(conn)

            # Verify that the extension was loaded
            assert result is True
            conn.execute.assert_any_call("INSTALL vss")
            conn.execute.assert_any_call("LOAD vss")

    @patch("autoresearch.extensions.ConfigLoader")
    def test_load_extension_download_failure_non_strict(self, mock_config_loader):
        """Test downloading and installing the extension fails but in non-strict mode."""
        # Configure the mock config loader
        mock_config = MagicMock()
        mock_config.config.storage.vector_extension_path = None
        mock_config_loader.return_value = mock_config

        # Create a mock connection
        conn = MagicMock()
        conn.execute.side_effect = Exception("Failed to install extension")

        # Mock os.getenv to return "false" for AUTORESEARCH_STRICT_EXTENSIONS
        with patch.dict(os.environ, {"AUTORESEARCH_STRICT_EXTENSIONS": "false"}):
            # Load the extension
            result = VSSExtensionLoader.load_extension(conn)

            # Verify that the extension was not loaded but no exception was raised
            assert result is False

    @patch("autoresearch.extensions.ConfigLoader")
    def test_load_extension_download_failure_strict(self, mock_config_loader):
        """Test downloading and installing the extension fails in strict mode."""
        # Configure the mock config loader
        mock_config = MagicMock()
        mock_config.config.storage.vector_extension_path = None
        mock_config_loader.return_value = mock_config

        # Create a mock connection
        conn = MagicMock()
        conn.execute.side_effect = Exception("Failed to install extension")

        # Mock os.getenv to return "true" for AUTORESEARCH_STRICT_EXTENSIONS
        with patch.dict(os.environ, {"AUTORESEARCH_STRICT_EXTENSIONS": "true"}):
            # Load the extension and expect a StorageError
            with pytest.raises(StorageError):
                VSSExtensionLoader.load_extension(conn)
