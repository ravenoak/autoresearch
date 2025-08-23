from __future__ import annotations

import importlib
import types
from typing import Any, Callable, cast

from fastapi import Request, Response
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from limits.util import parse
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import ConfigLoader, get_config
from .errors import handle_rate_limit
from .utils import RequestLogger, verify_bearer_token

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
        def __init__(self, *_, **__):
            self.limiter = types.SimpleNamespace(hit=lambda *_a, **_k: True)

        def _inject_headers(self, response: Response, *_a, **_k):
            return response

    def _fallback_rate_limit_exceeded_handler(*_a: Any, **_k: Any) -> Response:
        return PlainTextResponse("rate limit exceeded", status_code=429)

    class _FallbackLimit:  # pragma: no cover - simple stub
        def __init__(self, *_, **__):
            pass

    RateLimitExceeded = _FallbackRateLimitExceeded
    get_remote_address = _fallback_get_remote_address
    Limiter = _FallbackLimiter
    _rate_limit_exceeded_handler = _fallback_rate_limit_exceeded_handler
    Limit = _FallbackLimit


security = HTTPBearer(auto_error=False)


def dynamic_limit() -> str:
    limit = getattr(get_config().api, "rate_limit", 0)
    return f"{limit}/minute" if limit > 0 else "1000000/minute"


class AuthMiddleware(BaseHTTPMiddleware):
    """API key and token authentication middleware."""

    def _resolve_role(self, key: str | None, cfg) -> tuple[str, JSONResponse | None]:
        if cfg.api_keys:
            role = cfg.api_keys.get(key)
            if not role:
                return "anonymous", JSONResponse(
                    {"detail": "Invalid API key"}, status_code=401
                )
            return role, None
        if cfg.api_key:
            if key != cfg.api_key:
                return "anonymous", JSONResponse(
                    {"detail": "Invalid API key"}, status_code=401
                )
            return "user", None
        return "anonymous", None

    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/docs", "/openapi.json"}:
            return await call_next(request)
        loader = cast(ConfigLoader, request.app.state.config_loader)
        loader._config = loader.load_config()
        cfg = loader._config.api
        role, error = self._resolve_role(request.headers.get("X-API-Key"), cfg)
        if error:
            return error
        request.state.role = role
        request.state.permissions = set(cfg.role_permissions.get(role, []))
        if cfg.bearer_token:
            credentials: HTTPAuthorizationCredentials | None = await security(request)
            token = credentials.credentials if credentials else None
            if not token or not verify_bearer_token(token, cfg.bearer_token):
                return JSONResponse({"detail": "Invalid token"}, status_code=401)
        return await call_next(request)


class FallbackRateLimitMiddleware(BaseHTTPMiddleware):
    """Simplified rate limiting used when SlowAPI is unavailable."""

    def __init__(self, app, request_logger: RequestLogger, limiter: Limiter):
        super().__init__(app)
        self.request_logger = request_logger
        self.limiter = limiter

    async def dispatch(self, request: Request, call_next):
        cfg_limit = getattr(get_config().api, "rate_limit", 0)
        if cfg_limit:
            ip = get_remote_address(request)
            count = self.request_logger.log(ip)
            limit_obj = parse(dynamic_limit())
            request.state.view_rate_limit = (limit_obj, [ip])
            if count > cfg_limit:
                if SLOWAPI_STUB:
                    return handle_rate_limit(
                        request, RateLimitExceeded(cast("Limit", None))
                    )
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
            response = self.limiter._inject_headers(
                response, request.state.view_rate_limit
            )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting using SlowAPI's limiter with dynamic configuration."""

    def __init__(self, app, request_logger: RequestLogger, limiter: Limiter):
        super().__init__(app)
        self.request_logger = request_logger
        self.limiter = limiter

    async def dispatch(self, request: Request, call_next):
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
            return self.limiter._inject_headers(response, request.state.view_rate_limit)
        return await call_next(request)
