"""Typed stub for :mod:`matplotlib` and :mod:`matplotlib.pyplot`."""

from __future__ import annotations

import importlib.machinery
from types import ModuleType, SimpleNamespace
from typing import Any, Protocol, cast

from ._registry import install_stub_module


class MatplotlibModule(Protocol):
    __spec__: importlib.machinery.ModuleSpec

    def use(self, *args: Any, **kwargs: Any) -> None: ...


class MatplotlibPyplotModule(Protocol):
    __spec__: importlib.machinery.ModuleSpec

    def plot(self, *args: Any, **kwargs: Any) -> None: ...

    def figure(self, *args: Any, **kwargs: Any) -> None: ...

    def gca(self, *args: Any, **kwargs: Any) -> SimpleNamespace: ...

    def savefig(self, *args: Any, **kwargs: Any) -> None: ...


class _MatplotlibPyplotModule(ModuleType):
    __spec__ = importlib.machinery.ModuleSpec("matplotlib.pyplot", loader=None)

    def __init__(self) -> None:
        super().__init__("matplotlib.pyplot")

    def plot(self, *args: Any, **kwargs: Any) -> None:
        return None

    def figure(self, *args: Any, **kwargs: Any) -> None:
        return None

    def gca(self, *args: Any, **kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace()

    def savefig(self, *args: Any, **kwargs: Any) -> None:
        return None


class _MatplotlibModule(ModuleType):
    __spec__ = importlib.machinery.ModuleSpec("matplotlib", loader=None)

    def __init__(self) -> None:
        super().__init__("matplotlib")
        self.pyplot = cast(
            MatplotlibPyplotModule,
            install_stub_module("matplotlib.pyplot", _MatplotlibPyplotModule),
        )

    def use(self, *args: Any, **kwargs: Any) -> None:
        return None


matplotlib = cast(
    MatplotlibModule, install_stub_module("matplotlib", _MatplotlibModule)
)

__all__ = ["MatplotlibModule", "MatplotlibPyplotModule", "matplotlib"]
