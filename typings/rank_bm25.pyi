from __future__ import annotations

from collections.abc import Sequence
from typing import List

__all__ = ["BM25Okapi"]


class BM25Okapi:
    def __init__(self, corpus: Sequence[Sequence[str]] | Sequence[str]) -> None: ...

    def get_scores(self, query_tokens: Sequence[str]) -> List[float]: ...

    def get_batch_scores(
        self, query_tokens: Sequence[Sequence[str]]
    ) -> List[List[float]]: ...

    def get_top_n(
        self, query: Sequence[str], documents: Sequence[str], n: int
    ) -> List[str]: ...
