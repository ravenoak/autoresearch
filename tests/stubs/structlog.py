"""Minimal stub for the :mod:`structlog` package."""

import sys
import types

try:  # pragma: no cover - best effort to import real library
    import structlog as _structlog  # type: ignore
except Exception:  # pragma: no cover - fall back to stub
    structlog_stub = types.ModuleType("structlog")

    class BoundLogger:
        def __getattr__(self, _name):
            return lambda *a, **k: None

    def get_logger(*_args, **_kwargs):
        return BoundLogger()

    def configure(*args, **kwargs):  # noqa: D401 - simple placeholder
        """Stubbed configure function."""

    structlog_stub.BoundLogger = BoundLogger
    structlog_stub.get_logger = get_logger
    structlog_stub.configure = configure
    sys.modules["structlog"] = structlog_stub
else:  # pragma: no cover - real library available
    sys.modules["structlog"] = _structlog
