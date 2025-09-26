"""Typed stub for :mod:`numpy` used in tests."""

from __future__ import annotations

import importlib.util
from types import ModuleType
from typing import Any, Iterable, Protocol, cast

from ._registry import install_stub_module


def array(*args: Any, **kwargs: Any) -> list[Any]:
    if not args:
        return []
    value = args[0]
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return list(value)
    return []


def rand(*args: int, **kwargs: Any) -> list[float]:  # pragma: no cover - deterministic stub
    return []


class NumpyRandomModule(Protocol):
    def rand(self, *args: int, **kwargs: Any) -> Iterable[float]: ...


class _NumpyRandomModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("numpy.random")
        self._state: tuple[str, tuple[int, ...]] = ("stub", tuple())

    def rand(self, *args: int, **kwargs: Any) -> Iterable[float]:
        return rand(*args, **kwargs)

    def seed(self, *_args: Any, **_kwargs: Any) -> None:
        """Provide a deterministic seed hook for Hypothesis."""
        self._state = ("stub", tuple())

    def get_state(self) -> tuple[str, tuple[int, ...]]:
        return self._state

    def set_state(self, state: tuple[str, tuple[int, ...]]) -> None:
        self._state = state


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


# Export a manual stub instance for tests that temporarily replace ``numpy``.
numpy_stub = cast(NumpyModule, _factory())


__all__ = ["NumpyModule", "NumpyRandomModule", "array", "numpy", "numpy_stub", "rand"]
