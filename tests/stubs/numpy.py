"""Minimal stub for :mod:`numpy`.

Attempts to import the real package and falls back to a tiny stub when the
dependency is unavailable. The stub also exposes ``numpy.random`` so modules
expecting it can import without errors during tests.
"""

import sys
import types

try:
    import numpy as np  # type: ignore
except Exception:
    np = types.ModuleType("numpy")
    np.array = lambda *a, **k: []
    np.random = types.ModuleType("numpy.random")
    np.random.rand = lambda *a, **k: []

sys.modules["numpy"] = np
