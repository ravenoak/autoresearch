from __future__ import annotations

from typing import Any, Iterable


class Response:
    status_code: int
    media_type: str | None

    def __init__(self, content: Any = ..., *, status_code: int = 200, media_type: str | None = None, headers: dict[str, str] | None = None) -> None: ...


class PlainTextResponse(Response):
    ...


class JSONResponse(Response):
    ...


class StreamingResponse(Response):
    def __init__(
        self,
        content: Iterable[Any] | Any,
        *,
        status_code: int = 200,
        media_type: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None: ...


__all__ = [
    "JSONResponse",
    "PlainTextResponse",
    "Response",
    "StreamingResponse",
]
