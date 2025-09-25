"""Typed stub for :mod:`dspy`."""

from __future__ import annotations

import importlib.util
from types import ModuleType
from typing import Protocol, cast

from ._registry import install_stub_module


class DSPyModule(Protocol):
    __version__: str


class _DSPyModule(ModuleType):
    __version__ = "0.0"

    def __init__(self) -> None:
        super().__init__("dspy")


if importlib.util.find_spec("dspy") is None:
    dspy = cast(DSPyModule, install_stub_module("dspy", _DSPyModule))
else:  # pragma: no cover
    import dspy as _dspy

    dspy = cast(DSPyModule, _dspy)


__all__ = ["DSPyModule", "dspy"]
