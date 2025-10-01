"""Typed stub for :mod:`slowapi` used in tests."""

from __future__ import annotations

import inspect
import threading
from collections import Counter
from collections.abc import Awaitable, Callable, MutableMapping, Sequence
from types import ModuleType
from typing import Concatenate, Generic, ParamSpec, Protocol, TypeAlias, TypeVar, cast

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


TRequest = TypeVar("TRequest", bound="RequestProtocol")
P = ParamSpec("P")
ResultT = TypeVar("ResultT")



class RequestState(Protocol):
    view_rate_limit: object | None


class RequestProtocol(Protocol):
    client: object
    state: RequestState

    def __init__(self, scope: "Scope", receive: "ReceiveCallable") -> None: ...


class _LimiterBackend:
    def hit(self, *_args: object, **_kwargs: object) -> bool:
        return True


class Limiter(Generic[TRequest]):
    """Very small rate limiter used in tests."""

    IS_STUB = True

    def __init__(
        self,
        key_func: Callable[[TRequest], str] | None = None,
        application_limits: Sequence[str | Callable[[], str | int]] | None = None,
        request_log: RequestLog | None = None,
    ) -> None:
        self.key_func: Callable[[TRequest], str]
        if key_func is not None:
            self.key_func = key_func
        else:
            self.key_func = cast(Callable[[TRequest], str], lambda _request: "127.0.0.1")
        self.application_limits = list(application_limits or [])
        self.request_log = request_log or REQUEST_LOG
        self.limiter = _LimiterBackend()

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

    def check(
        self,
        request: TRequest,
        *,
        limit_override: str | Callable[[], str | int] | None = None,
    ) -> None:
        ip = self.key_func(request)
        count = self.request_log.log(ip)
        limit = 0
        if limit_override is not None:
            limit = self._parse_limit(limit_override)
        elif self.application_limits:
            limit = self._parse_limit(self.application_limits[0])
        if limit and count > limit:
            raise RateLimitExceeded()

    def limit(
        self, *limit_specs: str | Callable[[], str | int]
    ) -> Callable[
        [Callable[Concatenate[TRequest, P], Awaitable[ResultT]]],
        Callable[Concatenate[TRequest, P], Awaitable[ResultT]],
    ]:
        def decorator(
            func: Callable[Concatenate[TRequest, P], Awaitable[ResultT]]
        ) -> Callable[Concatenate[TRequest, P], Awaitable[ResultT]]:
            async def wrapper(
                request: TRequest, /, *args: P.args, **kwargs: P.kwargs
            ) -> ResultT:
                limit_override = limit_specs[0] if limit_specs else None
                self.check(request, limit_override=limit_override)
                return await func(request, *args, **kwargs)

            return cast(
                Callable[Concatenate[TRequest, P], Awaitable[ResultT]], wrapper
            )

        return decorator


def _rate_limit_exceeded_handler(_request: object, _exc: Exception) -> str:
    return "rate limit exceeded"


def reset_request_log() -> None:
    REQUEST_LOG.reset()


Message: TypeAlias = MutableMapping[str, object]
Scope: TypeAlias = MutableMapping[str, object]


class ReceiveCallable(Protocol):
    def __call__(self) -> Awaitable[Message]: ...


class SendCallable(Protocol):
    def __call__(self, message: Message) -> Awaitable[None]: ...
class ASGIApp(Protocol):
    def __call__(
        self, scope: Scope, receive: ReceiveCallable, send: SendCallable
    ) -> Awaitable[None]: ...


class SlowAPIMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        limiter: Limiter[RequestProtocol] | None = None,
    ) -> None:
        from starlette.requests import Request

        self.app = app
        self.limiter = limiter
        self.Request: type[RequestProtocol] = cast(type[RequestProtocol], Request)

    async def __call__(
        self,
        scope: Scope,
        receive: ReceiveCallable,
        send: SendCallable,
    ) -> None:
        if scope.get("type") == "http" and self.limiter:
            request = self.Request(scope, receive)
            self.limiter.check(request)
        await self.app(scope, receive, send)


def get_remote_address(scope: Scope) -> str:
    del scope
    return "127.0.0.1"


class SlowapiModule(Protocol):
    IS_STUB: bool
    Limiter: type[Limiter[RequestProtocol]]
    REQUEST_LOG: RequestLog

    def reset_request_log(self) -> None: ...

    def _rate_limit_exceeded_handler(
        self, request: RequestProtocol, exc: Exception
    ) -> str: ...


class _SlowapiModule(ModuleType):
    IS_STUB = True

    def __init__(self) -> None:
        super().__init__("slowapi")
        self.Limiter = Limiter
        self.REQUEST_LOG = REQUEST_LOG

    def reset_request_log(self) -> None:
        reset_request_log()

    def _rate_limit_exceeded_handler(
        self, request: RequestProtocol, exc: Exception
    ) -> str:
        return _rate_limit_exceeded_handler(request, exc)


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
    def get_remote_address(self, scope: Scope) -> str: ...


class _SlowapiUtilModule(ModuleType):
    def __init__(self) -> None:
        super().__init__("slowapi.util")

    def get_remote_address(self, scope: Scope) -> str:
        return get_remote_address(scope)


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
