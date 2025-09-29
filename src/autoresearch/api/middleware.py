from __future__ import annotations

import importlib
import types
from typing import Any, Awaitable, Callable, cast

from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from limits.util import parse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..config import get_config
from .auth_middleware import AuthMiddleware
from .errors import handle_rate_limit
from .utils import RequestLogger

# Lazily import SlowAPI and fall back to a minimal stub when unavailable
Limiter: Any
RateLimitExceeded: type[Exception]
_rate_limit_exceeded_handler: Callable[..., Response]
Limit: Any
get_remote_address: Callable[[Request], str]

try:  # pragma: no cover - optional dependency
    _slowapi_module = importlib.import_module("slowapi")
    SLOWAPI_STUB = getattr(_slowapi_module, "IS_STUB", False)
    from slowapi import Limiter as SlowLimiter
    from slowapi import _rate_limit_exceeded_handler as SlowHandler
    from slowapi.errors import RateLimitExceeded as SlowRateLimitExceeded
    from slowapi.util import get_remote_address as SlowGetRemoteAddress

    if not SLOWAPI_STUB:
        from slowapi.wrappers import Limit as SlowLimit

    Limiter = SlowLimiter
    RateLimitExceeded = SlowRateLimitExceeded
    _rate_limit_exceeded_handler = SlowHandler
    get_remote_address = SlowGetRemoteAddress
    if not SLOWAPI_STUB:
        Limit = SlowLimit
    else:
        Limit = type("Limit", (), {})
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    SLOWAPI_STUB = True

    class _FallbackRateLimitExceeded(Exception):
        """Fallback exception raised when the rate limit is exceeded."""

    def _fallback_get_remote_address(request: Request) -> str:
        return request.client.host if request.client else "unknown"

    class _FallbackLimiter:  # pragma: no cover - simple stub
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            self.limiter = types.SimpleNamespace(hit=lambda *_a, **_k: True)

        def _inject_headers(
            self, response: Response, *_args: object, **_kwargs: object
        ) -> Response:
            return response

    def _fallback_rate_limit_exceeded_handler(*_a: Any, **_k: Any) -> Response:
        return PlainTextResponse("rate limit exceeded", status_code=429)

    class _FallbackLimit:  # pragma: no cover - simple stub
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

    RateLimitExceeded = _FallbackRateLimitExceeded
    get_remote_address = _fallback_get_remote_address
    Limiter = _FallbackLimiter
    _rate_limit_exceeded_handler = _fallback_rate_limit_exceeded_handler
    Limit = _FallbackLimit


def dynamic_limit() -> str:
    limit = getattr(get_config().api, "rate_limit", 0)
    return f"{limit}/minute" if limit > 0 else "1000000/minute"


class FallbackRateLimitMiddleware(BaseHTTPMiddleware):
    """Simplified rate limiting used when SlowAPI is unavailable."""

    def __init__(
        self, app: ASGIApp, request_logger: RequestLogger, limiter: Limiter
    ) -> None:
        super().__init__(app)
        self.request_logger = request_logger
        self.limiter = limiter

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        cfg_limit = getattr(get_config().api, "rate_limit", 0)
        if cfg_limit:
            ip = get_remote_address(request)
            count = self.request_logger.log(ip)
            limit_obj = parse(dynamic_limit())
            request.state.view_rate_limit = (limit_obj, [ip])
            if count > cfg_limit:
                if SLOWAPI_STUB:
                    return handle_rate_limit(request, RateLimitExceeded(cast("Limit", None)))
                limit_wrapper = Limit(
                    limit_obj,
                    get_remote_address,
                    None,
                    False,
                    None,
                    None,
                    None,
                    1,
                    False,
                )
                return handle_rate_limit(request, RateLimitExceeded(limit_wrapper))
        response = await call_next(request)
        if cfg_limit and not SLOWAPI_STUB:
            response = cast(
                Response, self.limiter._inject_headers(response, request.state.view_rate_limit)
            )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting using SlowAPI's limiter with dynamic configuration."""

    def __init__(
        self, app: ASGIApp, request_logger: RequestLogger, limiter: Limiter
    ) -> None:
        super().__init__(app)
        self.request_logger = request_logger
        self.limiter = limiter

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        cfg_limit = getattr(get_config().api, "rate_limit", 0)
        if cfg_limit:
            ip = get_remote_address(request)
            count = self.request_logger.log(ip)
            limit_obj = parse(dynamic_limit())
            request.state.view_rate_limit = (limit_obj, [ip])
            if not self.limiter.limiter.hit(limit_obj, ip) or count > cfg_limit:
                limit_wrapper = Limit(
                    limit_obj,
                    get_remote_address,
                    None,
                    False,
                    None,
                    None,
                    None,
                    1,
                    False,
                )
                return handle_rate_limit(request, RateLimitExceeded(limit_wrapper))
            response = await call_next(request)
            return cast(
                Response, self.limiter._inject_headers(response, request.state.view_rate_limit)
            )
        return await call_next(request)


__all__ = [
    "AuthMiddleware",
    "FallbackRateLimitMiddleware",
    "RateLimitMiddleware",
    "Limiter",
    "RateLimitExceeded",
    "dynamic_limit",
    "get_remote_address",
]
