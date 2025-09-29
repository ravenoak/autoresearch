from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class Queue(Generic[T]):
    def __init__(self, maxsize: int | None = ...) -> None: ...

    def put(self, item: T, *, block: bool = ..., timeout: float | None = ...) -> None: ...

    def get(self, *, block: bool = ..., timeout: float | None = ...) -> T: ...

    def shutdown(self) -> None: ...


__all__ = ["Queue"]
