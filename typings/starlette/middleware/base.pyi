from __future__ import annotations

from typing import Any, Awaitable, Callable

from fastapi import Request
from fastapi.responses import Response
from starlette.types import ASGIApp

RequestResponseEndpoint = Callable[[Request], Awaitable[Response]]


class BaseHTTPMiddleware:
    app: ASGIApp

    def __init__(self, app: ASGIApp, dispatch: RequestResponseEndpoint | None = ...) -> None: ...

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response: ...


__all__ = ["BaseHTTPMiddleware", "RequestResponseEndpoint"]
