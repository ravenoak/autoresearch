"""Typed stub for :mod:`pdfminer`."""

from __future__ import annotations

import importlib.util
from types import ModuleType
from typing import Any, Protocol, cast

from ._registry import install_stub_module


def extract_text(*args: Any, **kwargs: Any) -> str:
    return ""


class PdfminerHighLevelModule(Protocol):
    def extract_text(self, *args: Any, **kwargs: Any) -> str: ...


class _PdfminerHighLevelModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("pdfminer.high_level")

    def extract_text(self, *args: Any, **kwargs: Any) -> str:
        return extract_text(*args, **kwargs)


class PdfminerModule(Protocol):
    high_level: PdfminerHighLevelModule
    __version__: str


class _PdfminerModule(ModuleType):
    __version__ = "0.0"

    def __init__(self) -> None:
        super().__init__("pdfminer")
        self.high_level = cast(
            PdfminerHighLevelModule,
            install_stub_module("pdfminer.high_level", _PdfminerHighLevelModule),
        )


if importlib.util.find_spec("pdfminer") is None:
    pdfminer = cast(PdfminerModule, install_stub_module("pdfminer", _PdfminerModule))
else:  # pragma: no cover
    import pdfminer as _pdfminer

    pdfminer = cast(PdfminerModule, _pdfminer)


__all__ = [
    "PdfminerHighLevelModule",
    "PdfminerModule",
    "extract_text",
    "pdfminer",
]
