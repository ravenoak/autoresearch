"""Error handling helpers for the Autoresearch API."""

from __future__ import annotations

from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response


def handle_rate_limit(request: Request, exc: Exception) -> Response:
    """Translate rate limit exceptions into HTTP responses."""
    from .middleware import _rate_limit_exceeded_handler

    result = _rate_limit_exceeded_handler(request, exc)
    if isinstance(result, Response):
        return result
    return PlainTextResponse(str(result), status_code=429)
