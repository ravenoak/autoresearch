from __future__ import annotations

from typing import Any, Iterable, Iterator


class Result(Iterable[tuple[Any, ...]]):
    bindings: list[dict[str, Any]]

    def __iter__(self) -> Iterator[tuple[Any, ...]]: ...


__all__ = ["Result"]
