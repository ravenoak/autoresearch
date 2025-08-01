"""Stub for the :mod:`kuzu` database library."""

import sys
import types

if "kuzu" not in sys.modules:
    kuzu_stub = types.ModuleType("kuzu")

    class _Result:
        def __init__(self, rows=None):
            self._rows = rows or []
            self._idx = 0

        def has_next(self):
            return self._idx < len(self._rows)

        def get_next(self):
            row = self._rows[self._idx]
            self._idx += 1
            return row

    class Database:
        def __init__(self, path):
            self.path = path

    class Connection:
        def __init__(self, db):
            self.db = db
            self.data = {}

        def execute(self, query, params=None):
            params = params or {}
            if "MERGE (c:Claim" in query:
                self.data[params["id"]] = (
                    params.get("content", ""),
                    params.get("conf", 0.0),
                )
                return _Result([])
            if "MATCH (c:Claim" in query:
                if params["id"] in self.data:
                    return _Result([self.data[params["id"]]])
                return _Result([])
            return _Result([])

        def close(self):
            pass

    kuzu_stub.Database = Database
    kuzu_stub.Connection = Connection
    sys.modules["kuzu"] = kuzu_stub
