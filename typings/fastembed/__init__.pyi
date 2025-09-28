from __future__ import annotations

from typing import Iterable, Sequence


class OnnxTextEmbedding:
    def __init__(self, *args: object, **kwargs: object) -> None: ...

    def embed(self, texts: Iterable[str]) -> Sequence[Sequence[float]]: ...


class TextEmbedding(OnnxTextEmbedding): ...


__all__ = ["OnnxTextEmbedding", "TextEmbedding"]
