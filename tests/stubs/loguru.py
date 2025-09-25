"""Typed stub for the :mod:`loguru` package."""

from __future__ import annotations

import importlib
from types import ModuleType, SimpleNamespace
from typing import Any, Dict, Protocol, cast

from ._registry import install_stub_module


class _Core:
    handlers: Dict[int, object]

    def __init__(self) -> None:
        self.handlers = {}


class Logger:
    _core: _Core

    def __init__(self) -> None:
        self._core = _Core()

    def add(self, *args: Any, **kwargs: Any) -> int:
        handler_id = len(self._core.handlers) + 1
        self._core.handlers[handler_id] = object()
        return handler_id

    def remove(self, *args: Any, **kwargs: Any) -> None:
        if args:
            self._core.handlers.pop(int(args[0]), None)

    def level(self, name: str) -> SimpleNamespace:
        return SimpleNamespace(name=name)

    def __getattr__(self, _name: str) -> Any:  # pragma: no cover - trivial
        return lambda *a, **k: None


class LoguruModule(Protocol):
    logger: Logger


class _LoguruModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("loguru")
        self.logger = Logger()


def _factory() -> _LoguruModule:
    return _LoguruModule()


try:  # pragma: no cover - use real library when available
    _loguru = importlib.import_module("loguru")
except Exception:  # pragma: no cover - fall back to stub
    loguru = cast(LoguruModule, install_stub_module("loguru", _factory))
else:  # pragma: no cover
    loguru = cast(LoguruModule, _loguru)


__all__ = ["Logger", "LoguruModule", "loguru"]
