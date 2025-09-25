"""Typed stub for :mod:`torch`."""

from __future__ import annotations

from types import ModuleType
from typing import Any, Protocol, cast

from unittest.mock import MagicMock

from ._registry import install_stub_module


class TorchModule(Protocol):
    def __getattr__(self, name: str) -> Any: ...


class _TorchModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("torch")

    def __getattr__(self, name: str) -> Any:
        return MagicMock(name=name)


torch = cast(TorchModule, install_stub_module("torch", _TorchModule))

__all__ = ["TorchModule", "torch"]
