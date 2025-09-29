from __future__ import annotations

from typing import Any, Protocol

__all__ = ["Image"]


class ImageType(Protocol):
    size: tuple[int, int]
    mode: str

    def save(self, fp: Any, format: str | None = ...) -> None: ...

    def close(self) -> None: ...


class ImageModule(Protocol):
    Image: type[ImageType]

    def open(self, fp: Any, mode: str = "r", formats: list[str] | None = ...) -> ImageType: ...


Image: ImageModule
