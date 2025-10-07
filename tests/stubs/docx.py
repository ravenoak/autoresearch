"""Typed stub for :mod:`docx`."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

from ._registry import install_stub_module


class Document:
    def __init__(self, path: str | Path | None = None) -> None:
        self.paragraphs: list[str] = []
        self.path = Path(path) if path else None

    def save(self, path: str | Path) -> None:
        Path(path).touch()


class DocxModule(Protocol):
    Document: type[Document]
    __version__: str


class _DocxModule(ModuleType):
    Document = Document
    __version__ = "0.0"
    __spec__ = importlib.util.spec_from_loader("docx", loader=None)

    def __init__(self) -> None:
        super().__init__("docx")


if importlib.util.find_spec("docx") is None:
    docx = cast(DocxModule, install_stub_module("docx", _DocxModule))
else:  # pragma: no cover
    try:
        import docx as _docx
    except Exception:  # pragma: no cover - dependency optional in CI image
        docx = cast(DocxModule, install_stub_module("docx", _DocxModule))
    else:
        docx = cast(DocxModule, _docx)


__all__ = ["DocxModule", "Document", "docx"]
