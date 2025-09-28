from __future__ import annotations

from typing import Any

from .language import Language


def load(name: str, *args: Any, **kwargs: Any) -> Language: ...


def blank(name: str) -> Language: ...


class cli:
    @staticmethod
    def download(name: str) -> None: ...


__all__ = ["Language", "blank", "cli", "load"]
