from __future__ import annotations

from typing import Any, Awaitable, Callable

from ...fastapi import Request
from ...fastapi import RequestResponseEndpoint
from ...fastapi.responses import Response


class BaseHTTPMiddleware:
    app: Any

    def __init__(self, app: Any, *args: Any, **kwargs: Any) -> None: ...

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response: ...

    async def __call__(self, scope: Any, receive: Callable[..., Awaitable[Any]], send: Callable[..., Awaitable[Any]]) -> None: ...


__all__ = ["BaseHTTPMiddleware", "RequestResponseEndpoint"]
