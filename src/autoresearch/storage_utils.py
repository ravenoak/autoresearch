"""Utility helpers for storage routines."""

from __future__ import annotations

from typing import Any

from .errors import StorageError
from .logging_utils import get_logger

log = get_logger(__name__)


def initialize_schema_version_without_fetchone(conn: Any) -> None:
    """Ensure the schema version exists in the metadata table.

    DuckDB cursors may lack :meth:`fetchone`, so this helper relies on
    :meth:`fetchall` to read existing values. If no version is present, it
    inserts ``1``.

    Args:
        conn: Active DuckDB connection.

    Raises:
        StorageError: If the schema version cannot be initialised.
    """
    try:
        execute_cls = getattr(conn.__class__, "execute", None)
        if execute_cls is not None:
            cursor = execute_cls(conn, "SELECT value FROM metadata WHERE key = 'schema_version'")
        else:
            cursor = conn.execute(
                "SELECT value FROM metadata WHERE key = 'schema_version'",
            )
        rows = cursor.fetchall() if hasattr(cursor, "fetchall") else []
        if not isinstance(rows, list) or not rows:
            log.info("Initializing schema version to 1")
            if execute_cls is not None:
                execute_cls(
                    conn,
                    "INSERT INTO metadata (key, value) VALUES ('schema_version', '1')",
                )
            else:
                conn.execute(
                    "INSERT INTO metadata (key, value) VALUES ('schema_version', '1')",
                )
    except Exception as exc:  # pragma: no cover - defensive
        raise StorageError("Failed to initialize schema version", cause=exc)


# Backward compatibility alias
initialize_schema_version = initialize_schema_version_without_fetchone
