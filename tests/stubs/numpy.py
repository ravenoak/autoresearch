"""Typed stub for :mod:`numpy` used in tests."""

from __future__ import annotations

import importlib.util
from types import ModuleType
from typing import Any, Iterable, Protocol, cast

from ._registry import install_stub_module


def array(*args: Any, **kwargs: Any) -> list[Any]:
    return list(args[0]) if args else []


def rand(*args: int, **kwargs: Any) -> list[float]:  # pragma: no cover - deterministic stub
    return [0.0] * (args[0] if args else 1)


class NumpyRandomModule(Protocol):
    def rand(self, *args: int, **kwargs: Any) -> Iterable[float]: ...


class _NumpyRandomModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("numpy.random")

    def rand(self, *args: int, **kwargs: Any) -> Iterable[float]:
        return rand(*args, **kwargs)


class NumpyModule(Protocol):
    random: NumpyRandomModule

    def array(self, *args: Any, **kwargs: Any) -> Iterable[Any]: ...


class _NumpyModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("numpy")
        self.random = cast(
            NumpyRandomModule, install_stub_module("numpy.random", _NumpyRandomModule)
        )

    def array(self, *args: Any, **kwargs: Any) -> Iterable[Any]:
        return array(*args, **kwargs)


def _factory() -> _NumpyModule:
    return _NumpyModule()


if importlib.util.find_spec("numpy") is None:  # pragma: no cover - dev env has numpy
    numpy = cast(NumpyModule, install_stub_module("numpy", _factory))
else:  # pragma: no cover
    import numpy as _numpy

    numpy = cast(NumpyModule, _numpy)


__all__ = ["NumpyModule", "NumpyRandomModule", "array", "numpy", "rand"]
