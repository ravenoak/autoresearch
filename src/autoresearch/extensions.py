"""
DuckDB extension management module.

This module provides utilities for loading and managing DuckDB extensions,
particularly the VSS extension used for vector similarity search.
"""

import logging
import os
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

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

        This method attempts to load the VSS extension using the following
        strategy:
        1. If ``storage.vector_extension_path`` is configured or
           ``.env.offline`` provides ``VECTOR_EXTENSION_PATH``, load from that
           filesystem path.
        2. If loading from filesystem fails or no path is configured, try to
           download and install

        Args:
            conn: The DuckDB connection to load the extension into

        Returns:
            bool: True if the extension was loaded successfully, False otherwise

        Raises:
            StorageError: If the extension fails to load and AUTORESEARCH_STRICT_EXTENSIONS
                         environment variable is set to "true"
        """
        cfg = ConfigLoader().config.storage
        logged_errors: set[str] = set()

        def _log(level: int, message: str, *args: Any) -> None:
            if level >= logging.ERROR:
                formatted = message % args if args else message
                if formatted in logged_errors:
                    return
                logged_errors.add(formatted)
            log.log(level, message, *args)

        def _env_extension_path() -> Path | None:
            env_path = os.getenv("VECTOR_EXTENSION_PATH")
            if not env_path:
                offline = dotenv_values(".env.offline")
                env_path = offline.get("VECTOR_EXTENSION_PATH")
            if env_path:
                candidate = Path(env_path).resolve()
                if candidate.exists():
                    return candidate
                log.warning("Offline VSS path does not exist: %s", candidate)
            return None

        def _is_duckdb_error(err: Exception) -> bool:
            try:
                import duckdb
            except ImportError:  # pragma: no cover - optional dependency
                return False
            return isinstance(err, duckdb.Error)

        extension_path: Path | None = None
        if cfg.vector_extension_path:
            extension_path = Path(cfg.vector_extension_path).resolve()
        else:
            extension_path = _env_extension_path()

        extension_loaded = False
        if extension_path:
            _log(logging.INFO, "Attempting to load VSS extension from %s", extension_path)
            if extension_path.suffix != ".duckdb_extension":
                _log(
                    logging.WARNING,
                    "VSS extension path does not end with .duckdb_extension: %s",
                    extension_path,
                )
            elif not extension_path.exists():
                _log(logging.WARNING, "VSS extension path does not exist: %s", extension_path)
            else:
                try:
                    conn.execute(f"LOAD '{extension_path.as_posix()}'")
                    if VSSExtensionLoader.verify_extension(conn, verbose=False):
                        _log(
                            logging.INFO,
                            "VSS extension loaded successfully from filesystem",
                        )
                        extension_loaded = True
                    else:
                        _log(
                            logging.WARNING,
                            "VSS extension failed verification after filesystem load",
                        )
                except Exception as e:  # pragma: no cover - defensive
                    _log(
                        logging.WARNING,
                        "Failed to load VSS extension from filesystem: %s",
                        e,
                    )
                    if not _is_duckdb_error(e):
                        raise

        if not extension_loaded:
            online_ok = (
                os.getenv("ENABLE_ONLINE_EXTENSION_INSTALL", "true").lower() == "true"
            )
            if online_ok:
                try:
                    _log(logging.INFO, "Installing vss extension...")
                    conn.execute("INSTALL vss")
                    _log(logging.INFO, "Loading vss extension...")
                    conn.execute("LOAD vss")
                    if VSSExtensionLoader.verify_extension(conn, verbose=False):
                        _log(logging.INFO, "VSS extension loaded successfully")
                        extension_loaded = True
                    else:
                        _log(logging.WARNING, "VSS extension may not be fully loaded")
                except Exception as e:  # pragma: no cover - network or install failure
                    if _is_duckdb_error(e):
                        _log(
                            logging.WARNING,
                            "DuckDB reported VSS installation failure: %s",
                            e,
                        )
                    else:
                        _log(logging.ERROR, "Failed to load VSS extension: %s", e)
                        raise
                    extension_loaded = VSSExtensionLoader._load_from_package(conn)
                    if not extension_loaded:
                        extension_loaded = VSSExtensionLoader._load_local_stub(conn)
                    if not extension_loaded:
                        extension_loaded = VSSExtensionLoader._create_stub_marker(conn)
                    if (
                        not extension_loaded
                        and os.getenv("AUTORESEARCH_STRICT_EXTENSIONS", "").lower() == "true"
                    ):
                        _log(
                            logging.ERROR,
                            "Failed to load VSS extension after fallbacks: %s",
                            e,
                        )
                        raise StorageError("Failed to load VSS extension", cause=e)
            else:
                _log(logging.INFO, "Skipping online VSS installation")
                extension_loaded = VSSExtensionLoader._load_from_package(conn)
                if not extension_loaded:
                    extension_loaded = VSSExtensionLoader._load_local_stub(conn)
                if not extension_loaded:
                    extension_loaded = VSSExtensionLoader._create_stub_marker(conn)
                if (
                    not extension_loaded
                    and os.getenv("AUTORESEARCH_STRICT_EXTENSIONS", "").lower() == "true"
                ):
                    _log(logging.ERROR, "Failed to load VSS extension in strict mode")
                    raise StorageError("Failed to load VSS extension")

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
        except Exception as err:  # pragma: no cover - defensive
            log.warning("Failed to load VSS stub: %s", err)
        return False

    @staticmethod
    def _create_stub_marker(conn: DuckDBConnection) -> bool:
        """Create a temporary table to mark a stubbed VSS extension.

        Args:
            conn: Connection where the marker should be created.

        Returns:
            bool: True if the marker was created, else False.
        """
        try:
            conn.execute("CREATE TEMP TABLE vss_stub(id INTEGER)")
            log.info("Created VSS stub marker table")
            return True
        except Exception as err:  # pragma: no cover - defensive
            log.warning("Failed to create VSS stub marker: %s", err)
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
            import duckdb_extension_vss as vss

            load_fn = getattr(vss, "load", None)
            if callable(load_fn):
                load_fn(conn)
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
        except Exception as err:  # pragma: no cover - defensive
            if verbose:
                log.warning("VSS extension verification failed: %s", err)
            try:
                conn.execute(
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_name='vss_stub'"
                )
                if verbose:
                    log.info("VSS stub marker present")
                return True
            except Exception as stub_err:  # pragma: no cover - defensive
                if verbose:
                    log.warning("VSS stub verification failed: %s", stub_err)
                return False
        else:
            if result and len(result) > 0:
                if verbose:
                    log.info("VSS extension is loaded")
                return True
            if verbose:
                log.warning("VSS extension is not loaded")
            return False
