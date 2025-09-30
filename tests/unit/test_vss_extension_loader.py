import logging
import os
from unittest.mock import MagicMock, call, patch

import duckdb
import pytest

from autoresearch.errors import StorageError
from autoresearch.extensions import VSSExtensionLoader
from pathlib import Path
from typing import Any


class TestVSSExtensionLoader:
    """Test the VSSExtensionLoader class."""

    @pytest.mark.real_vss
    def test_verify_extension_success(self) -> None:
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

    @pytest.mark.real_vss
    def test_verify_extension_failure(self) -> None:
        """Test that verify_extension returns False when the extension is not loaded."""
        # Create a mock connection that reports an empty extension list
        conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        conn.execute.return_value = mock_result

        # Verify that the extension is reported as not loaded
        assert VSSExtensionLoader.verify_extension(conn) is False
        conn.execute.assert_called_once_with(
            "SELECT * FROM duckdb_extensions() WHERE extension_name = 'vss'"
        )

    @pytest.mark.real_vss
    def test_verify_extension_fallback_to_stub_probe(self) -> None:
        """Fallback probe runs only when duckdb_extensions() raises."""
        conn = MagicMock()
        conn.execute.side_effect = [
            duckdb.Error("missing function"),
            MagicMock(),
        ]

        assert VSSExtensionLoader.verify_extension(conn) is True
        assert conn.execute.call_count == 2
        conn.execute.assert_has_calls(
            [
                call("SELECT * FROM duckdb_extensions() WHERE extension_name = 'vss'"),
                call(
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_name='vss_stub'"
                ),
            ]
        )

    @patch("autoresearch.extensions.ConfigLoader")
    def test_load_extension_from_filesystem_success(self, mock_config_loader: Any, tmp_path: Path) -> None:
        """Test loading the extension from the filesystem."""
        # Create a fake extension file
        fake_ext = tmp_path / "vss.duckdb_extension"
        fake_ext.touch()

        # Configure the mock config loader
        mock_config = MagicMock()
        mock_config.config.storage.vector_extension_path = str(fake_ext)
        mock_config_loader.return_value = mock_config

        # Create a mock connection
        conn = MagicMock()

        # Mock verify_extension to return True
        with patch.object(VSSExtensionLoader, "verify_extension", return_value=True):
            # Load the extension
            result = VSSExtensionLoader.load_extension(conn)

            # Verify that the extension was reported as loaded
            assert result is True

    @patch("autoresearch.extensions.ConfigLoader")
    def test_load_extension_from_filesystem_invalid_path(self, mock_config_loader: Any) -> None:
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

    @patch("autoresearch.extensions.ConfigLoader")
    def test_load_extension_from_filesystem_file_not_found(self, mock_config_loader: Any) -> None:
        """Test loading the extension from a non-existent filesystem path."""
        # Configure the mock config loader with a nonexistent path
        mock_config = MagicMock()
        mock_config.config.storage.vector_extension_path = "/path/to/vss.duckdb_extension"
        mock_config_loader.return_value = mock_config

        # Create a mock connection
        conn = MagicMock()

        # Mock the download and install to succeed
        with patch.object(VSSExtensionLoader, "verify_extension", return_value=True):
            # Load the extension
            result = VSSExtensionLoader.load_extension(conn)

            # Verify that the extension was loaded via download
            assert result is True

    @patch("autoresearch.extensions.ConfigLoader")
    def test_load_extension_from_filesystem_verification_failure(
        self, mock_config_loader: Any, tmp_path: Path
    ) -> None:
        """Test loading the extension from the filesystem but verification fails."""
        # Create a fake extension file
        fake_ext = tmp_path / "vss.duckdb_extension"
        fake_ext.touch()

        # Configure the mock config loader
        mock_config = MagicMock()
        mock_config.config.storage.vector_extension_path = str(fake_ext)
        mock_config_loader.return_value = mock_config

        # Create a mock connection
        conn = MagicMock()

        # Mock verify_extension to return False for filesystem but True for download
        with patch.object(
            VSSExtensionLoader, "verify_extension", side_effect=[False, True]
        ):
            # Load the extension
            result = VSSExtensionLoader.load_extension(conn)

            # Verify that the extension was loaded via download
            assert result is True

    @patch("autoresearch.extensions.ConfigLoader")
    def test_load_extension_download_success(self, mock_config_loader: Any) -> None:
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

    @pytest.mark.real_vss
    @patch("autoresearch.extensions.ConfigLoader")
    @pytest.mark.parametrize(
        ("package_result", "local_result", "marker_result", "expected_calls"),
        [
            (True, False, False, (1, 0, 0)),
            (False, True, False, (1, 1, 0)),
            (False, False, True, (1, 1, 1)),
        ],
        ids=("package", "local", "marker"),
    )
    def test_offline_fallbacks_quiet_logs(
        self,
        mock_config_loader: Any,
        caplog: pytest.LogCaptureFixture,
        package_result: Any,
        local_result: Any,
        marker_result: Any,
        expected_calls: Any,
    ) -> None:
        """Offline fallbacks avoid error-level logging."""

        mock_config = MagicMock()
        mock_config.config.storage.vector_extension_path = None
        mock_config_loader.return_value = mock_config

        conn = MagicMock()
        conn.execute.side_effect = duckdb.Error("offline")

        with patch.dict(os.environ, {"AUTORESEARCH_STRICT_EXTENSIONS": "false"}):
            with (
                patch.object(
                    VSSExtensionLoader,
                    "_load_from_package",
                    return_value=package_result,
                ) as load_package,
                patch.object(
                    VSSExtensionLoader,
                    "_load_local_stub",
                    return_value=local_result,
                ) as load_local,
                patch.object(
                    VSSExtensionLoader,
                    "_create_stub_marker",
                    return_value=marker_result,
                ) as create_marker,
                caplog.at_level(logging.INFO),
            ):
                assert VSSExtensionLoader.load_extension(conn) is True

        package_calls, local_calls, marker_calls = expected_calls
        assert load_package.call_count == package_calls
        assert load_local.call_count == local_calls
        assert create_marker.call_count == marker_calls
        assert not any(record.levelno >= logging.ERROR for record in caplog.records)

    @pytest.mark.real_vss
    @patch("autoresearch.extensions.ConfigLoader")
    def test_load_extension_download_failure_non_strict(
        self, mock_config_loader: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test downloading and installing the extension fails but in non-strict mode."""
        # Configure the mock config loader
        mock_config = MagicMock()
        mock_config.config.storage.vector_extension_path = None
        mock_config_loader.return_value = mock_config

        # Create a mock connection that raises a DuckDB error
        conn = MagicMock()
        conn.execute.side_effect = duckdb.Error("Failed to install extension")

        # Mock os.getenv to return "false" for AUTORESEARCH_STRICT_EXTENSIONS
        with patch.dict(os.environ, {"AUTORESEARCH_STRICT_EXTENSIONS": "false"}), caplog.at_level("ERROR"), patch(
            "pathlib.Path.exists", return_value=False
        ):
            # Load the extension
            result = VSSExtensionLoader.load_extension(conn)

            # Verify that the extension was not loaded but no exception was raised
            assert result is False

    @pytest.mark.real_vss
    @patch("autoresearch.extensions.ConfigLoader")
    def test_load_extension_download_failure_strict(self, mock_config_loader: Any) -> None:
        """Test downloading and installing the extension fails in strict mode."""
        # Configure the mock config loader
        mock_config = MagicMock()
        mock_config.config.storage.vector_extension_path = None
        mock_config_loader.return_value = mock_config

        # Create a mock connection
        conn = MagicMock()
        conn.execute.side_effect = duckdb.Error("Failed to install extension")

        # Mock os.getenv to return "true" for AUTORESEARCH_STRICT_EXTENSIONS
        with patch.dict(os.environ, {"AUTORESEARCH_STRICT_EXTENSIONS": "true"}):
            # Load the extension and expect a StorageError
            with pytest.raises(StorageError):
                VSSExtensionLoader.load_extension(conn)

    @pytest.mark.real_vss
    @patch("autoresearch.extensions.ConfigLoader")
    def test_load_extension_download_unhandled_exception(self, mock_config_loader: Any) -> None:
        """Non-duckdb errors propagate without being suppressed."""
        mock_config = MagicMock()
        mock_config.config.storage.vector_extension_path = None
        mock_config_loader.return_value = mock_config

        # Create a mock connection that raises an unexpected error
        conn = MagicMock()
        conn.execute.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            VSSExtensionLoader.load_extension(conn)

        assert conn.execute.call_count == 1

    @pytest.mark.real_vss
    @patch("autoresearch.extensions.ConfigLoader")
    def test_missing_extension_path_skips_loading(self, mock_config_loader: Any) -> None:
        """When configured path is missing, loading is skipped gracefully."""
        mock_config = MagicMock()
        mock_config.config.storage.vector_extension_path = "/nonexistent/vss.duckdb_extension"
        mock_config_loader.return_value = mock_config

        conn = MagicMock()
        conn.execute.side_effect = duckdb.Error("install fail")

        with patch.object(VSSExtensionLoader, "verify_extension", return_value=False):
            assert VSSExtensionLoader.load_extension(conn) is False

    @pytest.mark.real_vss
    @patch("autoresearch.extensions.ConfigLoader")
    def test_invalid_extension_file_skips_loading(self, mock_config_loader: Any, tmp_path: Path) -> None:
        """Invalid extension binaries are ignored and do not raise errors."""
        fake_ext = tmp_path / "vss.duckdb_extension"
        fake_ext.write_text("not a real extension")

        mock_config = MagicMock()
        mock_config.config.storage.vector_extension_path = str(fake_ext)
        mock_config_loader.return_value = mock_config

        conn = MagicMock()
        conn.execute.side_effect = [duckdb.Error("bad file"), duckdb.Error("install fail")]

        with patch.object(VSSExtensionLoader, "verify_extension", return_value=False):
            assert VSSExtensionLoader.load_extension(conn) is False
