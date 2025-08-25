"""Minimal stub of duckdb for tests."""


class Error(Exception):
    """Placeholder DuckDB exception."""


class DuckDBPyConnection:  # pragma: no cover - placeholder
    """Minimal DuckDB connection stub."""

    def execute(self, *args, **kwargs):
        return self

    def fetchall(self):
        return []

    def close(self):
        return None


def connect(*args, **kwargs):  # pragma: no cover - placeholder
    return DuckDBPyConnection()
