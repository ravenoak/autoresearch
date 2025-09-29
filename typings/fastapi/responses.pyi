from __future__ import annotations

from typing import Any, AsyncIterable, Iterable, Mapping


class Response:
    media_type: str | None
    status_code: int

    def __init__(
        self,
        content: Any = ...,
        status_code: int = ...,
        headers: Mapping[str, str] | None = ...,
        media_type: str | None = ...,
    ) -> None: ...

    def render(self, content: Any) -> bytes: ...


class JSONResponse(Response):
    def __init__(
        self,
        content: Any,
        status_code: int = ...,
        headers: Mapping[str, str] | None = ...,
        media_type: str | None = ...,
    ) -> None: ...


class PlainTextResponse(Response):
    def __init__(
        self,
        content: str,
        status_code: int = ...,
        headers: Mapping[str, str] | None = ...,
        media_type: str | None = ...,
    ) -> None: ...


class StreamingResponse(Response):
    def __init__(
        self,
        content: Iterable[bytes]
        | Iterable[str]
        | AsyncIterable[bytes]
        | AsyncIterable[str],
        status_code: int = ...,
        headers: Mapping[str, str] | None = ...,
        media_type: str | None = ...,
    ) -> None: ...


__all__ = [
    "JSONResponse",
    "PlainTextResponse",
    "Response",
    "StreamingResponse",
]
