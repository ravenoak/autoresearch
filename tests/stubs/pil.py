"""Typed stub for :mod:`PIL` and :mod:`PIL.Image`."""

from __future__ import annotations

import importlib.util
from types import ModuleType
from typing import Protocol, cast

from ._registry import install_stub_module


class Image:
    """Placeholder class for :class:`PIL.Image.Image`."""


class PILImageModule(Protocol):
    Image: type[Image]


class _PILImageModule(ModuleType):
    Image = Image

    def __init__(self) -> None:
        super().__init__("PIL.Image")


class PILModule(Protocol):
    Image: PILImageModule


class _PILModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("PIL")
        self.Image = cast(
            PILImageModule, install_stub_module("PIL.Image", _PILImageModule)
        )


if importlib.util.find_spec("PIL") is None:
    PIL = cast(PILModule, install_stub_module("PIL", _PILModule))
else:  # pragma: no cover
    import PIL as _PIL

    PIL = cast(PILModule, _PIL)


__all__ = ["Image", "PIL", "PILImageModule", "PILModule"]
