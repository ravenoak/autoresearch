"""Minimal stub for the :mod:`duckdb` package."""

import importlib.util
import sys
import types

if importlib.util.find_spec("duckdb") is None and "duckdb" not in sys.modules:
    duckdb_stub = types.ModuleType("duckdb")

    class _Conn:
        def __init__(self):
            self._rows: list = []

        def execute(self, *a, **k):
            return self

        def fetchall(self):
            return self._rows

        def fetchone(self):
            return self._rows[0] if self._rows else None

        def close(self):
            pass

    duckdb_stub.DuckDBPyConnection = _Conn
    duckdb_stub.connect = lambda *a, **k: _Conn()

    class Error(Exception):
        """Base DuckDB exception stub."""

    duckdb_stub.Error = Error
    sys.modules["duckdb"] = duckdb_stub
