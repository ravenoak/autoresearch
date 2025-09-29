from __future__ import annotations

from asyncio import Future
from contextlib import AbstractContextManager
from typing import Any, Awaitable, Callable, Iterable, Mapping, MutableMapping, Protocol

from autoresearch.api.utils import RequestLogger
from autoresearch.config import ConfigLoader
from .params import Depends as DependsDependency
from .responses import Response

Scope = Mapping[str, Any]
Receive = Callable[[], Awaitable[Any]]
Send = Callable[[dict[str, Any]], Awaitable[Any]]
RequestHandler = Callable[..., Any]
RouteDecorator = Callable[[RequestHandler], RequestHandler]


class FastAPIState(Protocol):
    limiter: Any
    request_logger: RequestLogger
    config_loader: ConfigLoader
    async_tasks: MutableMapping[str, Future[Any]]
    watch_ctx: AbstractContextManager[Any] | None

    def __setattr__(self, name: str, value: Any) -> None: ...


class RequestState(Protocol):
    permissions: set[str] | None
    www_authenticate: str
    view_rate_limit: tuple[Any, list[str]]
    role: str

    def __setattr__(self, name: str, value: Any) -> None: ...


class HTTPException(Exception):
    status_code: int
    detail: Any

    def __init__(
        self,
        status_code: int,
        detail: Any = ...,
        headers: Mapping[str, str] | None = ...,
    ) -> None: ...


class Request:
    app: Any
    state: RequestState
    scope: MutableMapping[str, Any]
    headers: Mapping[str, str]
    query_params: Mapping[str, str]
    path_params: MutableMapping[str, Any]
    client: Any
    url: Any

    def __init__(self, scope: Scope, receive: Receive, send: Send) -> None: ...


class APIRouter:
    routes: list[Any]

    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        methods: Iterable[str] | None = ...,
        name: str | None = ...,
        response_model: Any = ...,
    ) -> None: ...

    def include_router(self, router: APIRouter, *args: Any, **kwargs: Any) -> None: ...

    def get(self, path: str, *args: Any, **kwargs: Any) -> RouteDecorator: ...

    def post(self, path: str, *args: Any, **kwargs: Any) -> RouteDecorator: ...

    def put(self, path: str, *args: Any, **kwargs: Any) -> RouteDecorator: ...

    def delete(self, path: str, *args: Any, **kwargs: Any) -> RouteDecorator: ...


class FastAPI:
    router: APIRouter
    state: FastAPIState

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def add_middleware(self, middleware_class: type[Any], *args: Any, **kwargs: Any) -> None: ...

    def add_exception_handler(
        self,
        exc_class: type[BaseException],
        handler: Callable[[Request, BaseException], Awaitable[Response] | Response],
    ) -> None: ...

    def include_router(self, router: APIRouter, *args: Any, **kwargs: Any) -> None: ...

    def on_event(self, event_type: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...

    def get(self, path: str, *args: Any, **kwargs: Any) -> RouteDecorator: ...

    def post(self, path: str, *args: Any, **kwargs: Any) -> RouteDecorator: ...

    def put(self, path: str, *args: Any, **kwargs: Any) -> RouteDecorator: ...

    def delete(self, path: str, *args: Any, **kwargs: Any) -> RouteDecorator: ...


def Depends(
    dependency: Callable[..., Any] | None = ..., *, use_cache: bool = ...
) -> DependsDependency: ...


__all__ = [
    "APIRouter",
    "Depends",
    "FastAPI",
    "HTTPException",
    "Request",
    "Response",
]
