"""Typed stub for :mod:`pdfminer`."""

from __future__ import annotations

import importlib.util
from collections.abc import Container
from pathlib import Path
from types import ModuleType
from typing import IO, Protocol, cast

from ._registry import install_stub_module

PathLike = str | Path
BinaryIO = IO[bytes]


class LAParams(Protocol):
    char_margin: float | int
    line_margin: float | int


def extract_text(
    source: PathLike | BinaryIO,
    password: str = "",
    page_numbers: Container[int] | None = None,
    maxpages: int = 0,
    caching: bool = True,
    codec: str = "utf-8",
    laparams: LAParams | None = None,
) -> str:
    del source, password, page_numbers, maxpages, caching, codec, laparams
    return ""


class PdfminerHighLevelModule(Protocol):
    def extract_text(
        self,
        source: PathLike | BinaryIO,
        password: str = "",
        page_numbers: Container[int] | None = None,
        maxpages: int = 0,
        caching: bool = True,
        codec: str = "utf-8",
        laparams: LAParams | None = None,
    ) -> str:
        ...


class _PdfminerHighLevelModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("pdfminer.high_level")

    def extract_text(
        self,
        source: PathLike | BinaryIO,
        password: str = "",
        page_numbers: Container[int] | None = None,
        maxpages: int = 0,
        caching: bool = True,
        codec: str = "utf-8",
        laparams: LAParams | None = None,
    ) -> str:
        return extract_text(
            source,
            password=password,
            page_numbers=page_numbers,
            maxpages=maxpages,
            caching=caching,
            codec=codec,
            laparams=laparams,
        )


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
