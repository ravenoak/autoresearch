"""Minimal stub for the :mod:`tinydb` package."""

import sys
import types

if "tinydb" not in sys.modules:
    tinydb_stub = types.ModuleType("tinydb")

    class TinyDB:
        def __init__(self, *args, **kwargs):
            pass

        def close(self):
            pass

    class Query:
        pass

    tinydb_stub.TinyDB = TinyDB
    tinydb_stub.Query = Query
    sys.modules["tinydb"] = tinydb_stub
