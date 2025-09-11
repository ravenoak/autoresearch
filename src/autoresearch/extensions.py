"""
DuckDB extension management module.

This module provides utilities for loading and managing DuckDB extensions,
particularly the VSS extension used for vector similarity search.
"""

import os
from pathlib import Path
from typing import Any

import duckdb

from .config import ConfigLoader
from .errors import StorageError
from .logging_utils import get_logger

# Use "Any" for DuckDB connections due to incomplete upstream type hints.
DuckDBConnection = Any

log = get_logger(__name__)


class VSSExtensionLoader:
    """
    Handles loading and verification of the DuckDB VSS extension.

    This class encapsulates the logic for loading the VSS extension from
    a local file or downloading it from the DuckDB extension repository.
    It provides methods for verifying that the extension is loaded correctly
    and handles fallback strategies when loading fails.
    """

    @staticmethod
    def load_extension(conn: DuckDBConnection) -> bool:
        """Load the VSS extension into the provided DuckDB connection.

        This method attempts to load the VSS extension using the following strategy:
        1. If vector_extension_path is configured, try to load from filesystem
        2. If loading from filesystem fails or no path is configured, try to download and install

        Args:
            conn: The DuckDB connection to load the extension into

        Returns:
            bool: True if the extension was loaded successfully, False otherwise

        Raises:
            StorageError: If the extension fails to load and AUTORESEARCH_STRICT_EXTENSIONS
                         environment variable is set to "true"
        """
        cfg = ConfigLoader().config.storage

        extension_loaded = False
        if cfg.vector_extension_path:
            extension_path = Path(cfg.vector_extension_path).resolve()
            log.info(f"Attempting to load VSS extension from {extension_path}")
            if extension_path.suffix != ".duckdb_extension":
                log.warning(
                    "VSS extension path does not end with .duckdb_extension: %s",
                    extension_path,
                )
            elif not extension_path.exists():
                log.warning("VSS extension path does not exist: %s", extension_path)
            else:
                try:
                    conn.execute(f"LOAD '{extension_path.as_posix()}'")
                    if VSSExtensionLoader.verify_extension(conn, verbose=False):
                        log.info("VSS extension loaded successfully from filesystem")
                        extension_loaded = True
                    else:
                        log.warning("VSS extension failed verification after filesystem load")
                except duckdb.Error as e:  # type: ignore[attr-defined]
                    log.warning("Failed to load VSS extension from filesystem: %s", e)

        if not extension_loaded:
            try:
                log.info("Installing vss extension...")
                conn.execute("INSTALL vss")
                log.info("Loading vss extension...")
                conn.execute("LOAD vss")
                if VSSExtensionLoader.verify_extension(conn, verbose=False):
                    log.info("VSS extension loaded successfully")
                    extension_loaded = True
                else:
                    log.warning("VSS extension may not be fully loaded")
            except duckdb.Error as e:  # type: ignore[attr-defined]
                log.error("Failed to load VSS extension: %s", e)
                extension_loaded = VSSExtensionLoader._load_from_package(conn)
                if not extension_loaded:
                    extension_loaded = VSSExtensionLoader._load_local_stub(conn)
                if (
                    not extension_loaded
                    and os.getenv("AUTORESEARCH_STRICT_EXTENSIONS", "").lower() == "true"
                ):
                    raise StorageError("Failed to load VSS extension", cause=e)

        return extension_loaded

    @staticmethod
    def _load_local_stub(conn: DuckDBConnection) -> bool:
        """Attempt to load the stubbed VSS extension from the repository.

        Args:
            conn: DuckDB connection to receive the extension.

        Returns:
            bool: True if the stub loaded and verified, else False.
        """
        stub_path = (
            Path(__file__).resolve().parents[2] / "extensions" / "vss" / "vss.duckdb_extension"
        )
        if not stub_path.exists():
            log.warning("VSS stub not found at %s", stub_path)
            return False
        try:
            log.info("Loading VSS stub from %s", stub_path)
            conn.execute(f"LOAD '{stub_path.as_posix()}'")
            if VSSExtensionLoader.verify_extension(conn, verbose=False):
                log.info("VSS stub extension loaded")
                return True
            log.warning("VSS stub failed verification")
        except duckdb.Error as err:  # type: ignore[attr-defined]
            log.warning("Failed to load VSS stub: %s", err)
        return False

    @staticmethod
    def _load_from_package(conn: DuckDBConnection) -> bool:
        """Attempt to load the VSS extension from the Python package.

        The ``duckdb_extension_vss`` package ships prebuilt binaries for common
        platforms. When available, its loader is used before falling back to a
        stubbed extension.

        Args:
            conn: DuckDB connection to receive the extension.

        Returns:
            bool: True if the package provided the extension, else False.
        """
        try:
            import duckdb_extension_vss as vss  # type: ignore[import-not-found]

            if hasattr(vss, "load"):
                vss.load(conn)  # type: ignore[attr-defined]
                return VSSExtensionLoader.verify_extension(conn, verbose=False)
            path = Path(getattr(vss, "__file__", "")).parent / "vss.duckdb_extension"
            if path.exists():
                conn.execute(f"LOAD '{path.as_posix()}'")
                return VSSExtensionLoader.verify_extension(conn, verbose=False)
            log.warning("duckdb_extension_vss package lacks load() and extension file")
        except Exception as err:  # pragma: no cover - optional dependency
            log.warning("Failed to load VSS extension from package: %s", err)
        return False

    @staticmethod
    def verify_extension(conn: DuckDBConnection, verbose: bool = True) -> bool:
        """
        Verify that the VSS extension is loaded and functioning correctly.

        This method checks if the VSS extension is loaded by querying the
        duckdb_extensions() function and checking if the VSS extension is in the list.

        Args:
            conn: The DuckDB connection to check
            verbose: Whether to log detailed messages (default: True)

        Returns:
            bool: True if the extension is loaded and functioning, False otherwise
        """
        try:
            result = conn.execute(
                "SELECT * FROM duckdb_extensions() WHERE extension_name = 'vss'"
            ).fetchall()
            if result and len(result) > 0:
                if verbose:
                    log.info("VSS extension is loaded")
                return True
            else:
                if verbose:
                    log.warning("VSS extension is not loaded")
                return False
        except duckdb.Error as e:  # type: ignore[attr-defined]
            if verbose:
                log.warning(f"VSS extension verification failed: {e}")
            return False
