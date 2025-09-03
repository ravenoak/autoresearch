"""Minimal stub for :mod:`docx` to avoid optional dependency."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


class _Document:
    def __init__(self, path: str | Path | None = None) -> None:
        self.paragraphs: list[str] = []
        self.path = Path(path) if path else None

    def save(self, path: str | Path) -> None:
        Path(path).touch()


if "docx" not in sys.modules:
    module = ModuleType("docx")
    module.Document = _Document
    module.__version__ = "0.0"
    module.__spec__ = importlib.util.spec_from_loader("docx", loader=None)
    sys.modules["docx"] = module
