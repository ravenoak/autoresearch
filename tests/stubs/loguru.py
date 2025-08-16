"""Minimal stub for the :mod:`loguru` package."""

import sys
import types

try:  # pragma: no cover - prefer real library if available
    import loguru as _loguru  # type: ignore
except Exception:  # pragma: no cover - fall back to stub
    loguru_stub = types.ModuleType("loguru")

    class _Core:
        handlers: dict[int, object] = {}

    class _Logger:
        _core = _Core()

        def add(self, *args, **kwargs) -> int:  # noqa: D401 - placeholder
            handler_id = len(self._core.handlers) + 1
            self._core.handlers[handler_id] = object()
            return handler_id

        def remove(self, *args, **kwargs) -> None:  # noqa: D401 - placeholder
            if args:
                self._core.handlers.pop(args[0], None)

        def level(self, name: str):  # noqa: D401 - placeholder
            return types.SimpleNamespace(name=name)

        def __getattr__(self, _name):
            return lambda *a, **k: None

    loguru_stub.logger = _Logger()
    sys.modules["loguru"] = loguru_stub
else:  # pragma: no cover - real library available
    sys.modules["loguru"] = _loguru
