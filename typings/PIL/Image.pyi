from __future__ import annotations

from typing import Any

__all__ = ["Image", "open", "new"]


class Image:
    size: tuple[int, int]
    mode: str

    def save(self, fp: Any, format: str | None = ...) -> None: ...

    def close(self) -> None: ...


def open(fp: Any, mode: str = "r", formats: list[str] | None = ...) -> Image: ...


def new(mode: str, size: tuple[int, int], color: Any = ...) -> Image: ...
