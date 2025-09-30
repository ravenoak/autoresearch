"""Typed stub for :mod:`pdfminer`."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import IO, Iterable, Literal, Protocol, cast

from ._registry import install_stub_module

PathLike = str | Path
TextIO = IO[str]
BinaryIO = IO[bytes]


def extract_text(
    source: PathLike | BinaryIO,
    *,
    outfile: PathLike | TextIO | None = None,
    laparams: object | None = None,
    output_type: Literal["text", "html", "xml", "tag"] = "text",
    codec: str = "utf-8",
    caching: bool = True,
    maxpages: int = 0,
    password: str = "",
    pagenos: Iterable[int] | None = None,
) -> str:
    del source, outfile, laparams, output_type, codec
    del caching, maxpages, password, pagenos
    return ""


class PdfminerHighLevelModule(Protocol):
    def extract_text(
        self,
        source: PathLike | BinaryIO,
        *,
        outfile: PathLike | TextIO | None = None,
        laparams: object | None = None,
        output_type: Literal["text", "html", "xml", "tag"] = "text",
        codec: str = "utf-8",
        caching: bool = True,
        maxpages: int = 0,
        password: str = "",
        pagenos: Iterable[int] | None = None,
    ) -> str:
        ...


class _PdfminerHighLevelModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("pdfminer.high_level")

    def extract_text(
        self,
        source: PathLike | BinaryIO,
        *,
        outfile: PathLike | TextIO | None = None,
        laparams: object | None = None,
        output_type: Literal["text", "html", "xml", "tag"] = "text",
        codec: str = "utf-8",
        caching: bool = True,
        maxpages: int = 0,
        password: str = "",
        pagenos: Iterable[int] | None = None,
    ) -> str:
        return extract_text(
            source,
            outfile=outfile,
            laparams=laparams,
            output_type=output_type,
            codec=codec,
            caching=caching,
            maxpages=maxpages,
            password=password,
            pagenos=pagenos,
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
