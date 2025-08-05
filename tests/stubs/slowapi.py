"""Stub implementation for the :mod:`slowapi` rate limiting package."""

import sys
import types
import threading
from collections import Counter

slowapi_stub = types.ModuleType("slowapi")
slowapi_stub.IS_STUB = True

REQUEST_LOG: Counter[str] = Counter()
REQUEST_LOG_LOCK = threading.Lock()


class RateLimitExceeded(Exception):
    """Exception raised when a rate limit is exceeded."""


class Limiter:
    """Very small rate limiter used in tests."""

    IS_STUB = True

    def __init__(self, key_func=None, application_limits=None):
        self.key_func = key_func or (lambda r: "127.0.0.1")
        self.application_limits = application_limits or []

    def _parse_limit(self, spec):
        if callable(spec):
            spec = spec()
        try:
            return int(str(spec).split("/")[0])
        except Exception:
            return 0

    def check(self, request):  # pragma: no cover - simple stub
        ip = self.key_func(request)
        with REQUEST_LOG_LOCK:
            REQUEST_LOG[ip] += 1
            count = REQUEST_LOG[ip]
        limit = 0
        if self.application_limits:
            limit = self._parse_limit(self.application_limits[0])
        if limit and count > limit:
            raise RateLimitExceeded()

    def limit(self, *_args, **_kwargs):  # pragma: no cover - simple stub
        def decorator(func):
            def wrapper(request, *a, **k):
                self.check(request)
                return func(request, *a, **k)

            return wrapper

        return decorator


def _rate_limit_exceeded_handler(*_a, **_k):
    return "rate limit exceeded"


class SlowAPIMiddleware:  # pragma: no cover - simple stub
    def __init__(self, app, limiter=None, *_, **__):
        from starlette.requests import Request

        self.app = app
        self.limiter = limiter
        self.Request = Request

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http" and self.limiter:
            req = self.Request(scope, receive=receive)
            self.limiter.check(req)
        await self.app(scope, receive, send)


def get_remote_address(*_a, **_k):
    return "127.0.0.1"


slowapi_stub.Limiter = Limiter
slowapi_stub.REQUEST_LOG = REQUEST_LOG
slowapi_stub.REQUEST_LOG_LOCK = REQUEST_LOG_LOCK
slowapi_stub._rate_limit_exceeded_handler = _rate_limit_exceeded_handler

errors_mod = types.ModuleType("slowapi.errors")
errors_mod.RateLimitExceeded = RateLimitExceeded
middleware_mod = types.ModuleType("slowapi.middleware")
middleware_mod.SlowAPIMiddleware = SlowAPIMiddleware
util_mod = types.ModuleType("slowapi.util")
util_mod.get_remote_address = get_remote_address

sys.modules["slowapi"] = slowapi_stub
sys.modules["slowapi.errors"] = errors_mod
sys.modules["slowapi.middleware"] = middleware_mod
sys.modules["slowapi.util"] = util_mod
