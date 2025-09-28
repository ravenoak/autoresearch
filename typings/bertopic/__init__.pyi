from __future__ import annotations

from typing import Any, Iterable, Sequence


class BERTopic:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def fit_transform(self, documents: Iterable[str]) -> tuple[Sequence[int], Sequence[list[str]]]: ...


__all__ = ["BERTopic"]
