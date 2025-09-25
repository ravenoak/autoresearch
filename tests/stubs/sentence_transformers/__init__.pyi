from __future__ import annotations

from typing import Any, Sequence


class SentenceTransformer:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def encode(
        self, sentences: Sequence[str] | str, *args: Any, **kwargs: Any
    ) -> Any: ...

    def embed(
        self, sentences: Sequence[str] | str, *args: Any, **kwargs: Any
    ) -> Any: ...


__all__ = ["SentenceTransformer"]
