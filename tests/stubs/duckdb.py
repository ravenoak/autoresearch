"""Minimal stub for the :mod:`duckdb` package."""

import sys
import types

if "duckdb" not in sys.modules:
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
    sys.modules["duckdb"] = duckdb_stub
