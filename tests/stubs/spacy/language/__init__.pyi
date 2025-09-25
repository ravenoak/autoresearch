from __future__ import annotations

from typing import Iterable, Iterator, Protocol


class Span(Protocol):
    text: str
    label_: str


class Doc(Protocol):
    ents: Iterable[Span]


class Language:
    def __call__(self, text: str) -> Doc: ...

    def pipe(self, texts: Iterable[str]) -> Iterator[Doc]: ...
