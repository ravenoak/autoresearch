"""Typed stub for the :mod:`structlog` package."""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any, Callable, ClassVar, Protocol, cast

from ._registry import install_stub_module


class BoundLogger:
    def __getattr__(self, _name: str) -> Callable[..., None]:  # pragma: no cover - trivial
        return lambda *args, **kwargs: None


class StructlogModule(Protocol):
    BoundLogger: ClassVar[type[BoundLogger]]

    def get_logger(self, *args: Any, **kwargs: Any) -> BoundLogger: ...

    def configure(self, *args: Any, **kwargs: Any) -> None: ...

    def make_filtering_bound_logger(self, level: Any) -> type[BoundLogger]: ...


class _StructlogModule(ModuleType):
    BoundLogger: ClassVar[type[BoundLogger]] = BoundLogger

    def __init__(self) -> None:
        super().__init__("structlog")

    def get_logger(self, *args: Any, **kwargs: Any) -> BoundLogger:
        return BoundLogger()

    def configure(self, *args: Any, **kwargs: Any) -> None:
        return None

    def make_filtering_bound_logger(self, level: Any) -> type[BoundLogger]:
        return BoundLogger


def _factory() -> _StructlogModule:
    return _StructlogModule()


try:  # pragma: no cover
    _structlog = importlib.import_module("structlog")
except Exception:  # pragma: no cover
    structlog = cast(StructlogModule, install_stub_module("structlog", _factory))
else:  # pragma: no cover
    structlog = cast(StructlogModule, _structlog)


__all__ = [
    "BoundLogger",
    "StructlogModule",
    "structlog",
]
