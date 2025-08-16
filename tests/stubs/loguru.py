"""Minimal stub for the :mod:`loguru` package."""

import sys
import types

if "loguru" not in sys.modules:
    loguru_stub = types.ModuleType("loguru")

    class _Logger:
        def __getattr__(self, _name):
            return lambda *a, **k: None

    loguru_stub.logger = _Logger()
    sys.modules["loguru"] = loguru_stub
