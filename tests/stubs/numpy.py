"""Minimal stub for the :mod:`numpy` package."""

import sys
import types

if "numpy" not in sys.modules:
    np_stub = types.ModuleType("numpy")
    np_stub.array = lambda *a, **k: []
    sys.modules["numpy"] = np_stub
