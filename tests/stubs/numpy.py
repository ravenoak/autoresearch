"""Minimal stub for :mod:`numpy`.

Registers a tiny stand-in only when the real package cannot be found. The stub
also exposes ``numpy.random`` so modules expecting it can import without errors
during tests.  When the real package exists, it is left untouched and the stub
is available as ``numpy_stub`` for tests that need to install it manually via
``sys.modules``.
"""

import importlib.util
import sys
import types

numpy_stub = types.ModuleType("numpy")
numpy_stub.array = lambda *a, **k: []
numpy_stub.random = types.ModuleType("numpy.random")
numpy_stub.random.rand = lambda *a, **k: []

if importlib.util.find_spec("numpy") is None:  # pragma: no cover - real package present in dev env
    sys.modules["numpy"] = numpy_stub
    sys.modules["numpy.random"] = numpy_stub.random
