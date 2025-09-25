from __future__ import annotations

from typing import Any, Sequence


class BERTopic:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def fit_transform(
        self, documents: Sequence[str]
    ) -> tuple[list[int], list[Any]]: ...

    def transform(
        self, documents: Sequence[str]
    ) -> tuple[list[int], list[Any]]: ...


__all__ = ["BERTopic"]
