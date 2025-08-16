"""Minimal stub for the :mod:`structlog` package."""

import sys
import types

if "structlog" not in sys.modules:
    structlog_stub = types.ModuleType("structlog")

    class BoundLogger:
        def __getattr__(self, _name):
            return lambda *a, **k: None

    def get_logger(*_args, **_kwargs):
        return BoundLogger()

    structlog_stub.BoundLogger = BoundLogger
    structlog_stub.get_logger = get_logger
    sys.modules["structlog"] = structlog_stub
