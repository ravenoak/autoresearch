from __future__ import annotations

from typing import Any, Iterable, Sequence


class SentenceTransformer:
    def __init__(self, model_name_or_path: str | None = ..., *args: Any, **kwargs: Any) -> None: ...

    def encode(
        self,
        sentences: Iterable[str],
        *,
        batch_size: int = ...,
        show_progress_bar: bool = ...,
    ) -> Sequence[Sequence[float]]: ...


__all__ = ["SentenceTransformer"]
