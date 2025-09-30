"""Typed stub for :mod:`slowapi` used in tests."""

from __future__ import annotations

import threading
from collections import Counter
from collections.abc import Awaitable
from types import ModuleType
from typing import Any, Callable, Protocol, TypeAlias, cast

from ._registry import install_stub_module


class RequestLog:
    """Thread-safe request counter used by the stub limiter."""

    def __init__(self) -> None:
        self._log: Counter[str] = Counter()
        self._lock = threading.Lock()

    def log(self, ip: str) -> int:
        with self._lock:
            self._log[ip] += 1
            return self._log[ip]

    def reset(self) -> None:
        with self._lock:
            self._log.clear()


REQUEST_LOG = RequestLog()


class RateLimitExceeded(Exception):
    """Exception raised when a rate limit is exceeded."""


class Limiter:
    """Very small rate limiter used in tests."""

    IS_STUB = True

    def __init__(
        self,
        key_func: Callable[[Any], str] | None = None,
        application_limits: list[str] | None = None,
        request_log: RequestLog | None = None,
    ) -> None:
        self.key_func = key_func or (lambda _request: "127.0.0.1")
        self.application_limits = application_limits or []
        self.request_log = request_log or REQUEST_LOG

    def _parse_limit(self, spec: str | Callable[[], str | int]) -> int:
        value: str | int
        if callable(spec):
            value = spec()
        else:
            value = spec
        try:
            return int(str(value).split("/")[0])
        except Exception:
            return 0

    def check(self, request: Any) -> None:
        ip = self.key_func(request)
        count = self.request_log.log(ip)
        limit = 0
        if self.application_limits:
            limit = self._parse_limit(self.application_limits[0])
        if limit and count > limit:
            raise RateLimitExceeded()

    def limit(
        self, *_args: Any, **_kwargs: Any
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
                self.check(request)
                return func(request, *args, **kwargs)

            return wrapper

        return decorator


def _rate_limit_exceeded_handler(*_args: Any, **_kwargs: Any) -> str:
    return "rate limit exceeded"


def reset_request_log() -> None:
    REQUEST_LOG.reset()


class ReceiveCallable(Protocol):
    def __call__(self) -> Awaitable[dict[str, Any]]: ...


class SendCallable(Protocol):
    def __call__(self, message: dict[str, Any]) -> Awaitable[None]: ...


Scope: TypeAlias = dict[str, Any]
ASGIApp: TypeAlias = Callable[[Scope, ReceiveCallable, SendCallable], Awaitable[None]]


class SlowAPIMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        limiter: Limiter | None = None,
        *_args: Any,
        **_kwargs: Any,
    ) -> None:
        from starlette.requests import Request

        self.app = app
        self.limiter = limiter
        self.Request = Request

    async def __call__(
        self,
        scope: Scope,
        receive: ReceiveCallable,
        send: SendCallable,
    ) -> None:
        if scope.get("type") == "http" and self.limiter:
            request = self.Request(scope, receive=receive)
            self.limiter.check(request)
        await self.app(scope, receive, send)


def get_remote_address(*_args: Any, **_kwargs: Any) -> str:
    return "127.0.0.1"


class SlowapiModule(Protocol):
    IS_STUB: bool
    Limiter: type[Limiter]
    REQUEST_LOG: RequestLog

    def reset_request_log(self) -> None: ...

    def _rate_limit_exceeded_handler(self, *_args: Any, **_kwargs: Any) -> str: ...


class _SlowapiModule(ModuleType):
    IS_STUB = True

    def __init__(self) -> None:
        super().__init__("slowapi")
        self.Limiter = Limiter
        self.REQUEST_LOG = REQUEST_LOG

    def reset_request_log(self) -> None:
        reset_request_log()

    def _rate_limit_exceeded_handler(self, *_args: Any, **_kwargs: Any) -> str:
        return _rate_limit_exceeded_handler(*_args, **_kwargs)


class SlowapiErrorsModule(Protocol):
    RateLimitExceeded: type[RateLimitExceeded]


class _SlowapiErrorsModule(ModuleType):
    RateLimitExceeded = RateLimitExceeded

    def __init__(self) -> None:
        super().__init__("slowapi.errors")


class SlowapiMiddlewareModule(Protocol):
    SlowAPIMiddleware: type[SlowAPIMiddleware]


class _SlowapiMiddlewareModule(ModuleType):
    SlowAPIMiddleware = SlowAPIMiddleware

    def __init__(self) -> None:
        super().__init__("slowapi.middleware")


class SlowapiUtilModule(Protocol):
    def get_remote_address(self, *_args: Any, **_kwargs: Any) -> str: ...


class _SlowapiUtilModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("slowapi.util")

    def get_remote_address(self, *_args: Any, **_kwargs: Any) -> str:
        return get_remote_address(*_args, **_kwargs)


slowapi = cast(SlowapiModule, install_stub_module("slowapi", _SlowapiModule))
errors = cast(
    SlowapiErrorsModule, install_stub_module("slowapi.errors", _SlowapiErrorsModule)
)
middleware = cast(
    SlowapiMiddlewareModule,
    install_stub_module("slowapi.middleware", _SlowapiMiddlewareModule),
)
util = cast(SlowapiUtilModule, install_stub_module("slowapi.util", _SlowapiUtilModule))

setattr(slowapi, "errors", errors)
setattr(slowapi, "middleware", middleware)
setattr(slowapi, "util", util)

__all__ = [
    "Limiter",
    "RateLimitExceeded",
    "RequestLog",
    "SlowAPIMiddleware",
    "slowapi",
]
