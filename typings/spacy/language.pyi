from __future__ import annotations

from typing import Iterable, Protocol


class Span(Protocol):
    text: str
    label_: str


class Doc:
    ents: Iterable[Span]

    def __call__(self, text: str) -> Doc: ...


class Language:
    def __call__(self, text: str) -> Doc: ...

    def add_pipe(self, name: str, *args: object, **kwargs: object) -> None: ...


__all__ = ["Doc", "Language", "Span"]
