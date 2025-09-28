from __future__ import annotations

from typing import Any, Awaitable, Callable, Iterable, Mapping, MutableMapping

from .responses import Response

Scope = Mapping[str, Any]
Receive = Callable[[], Awaitable[Any]]
Send = Callable[[dict[str, Any]], Awaitable[Any]]
RequestHandler = Callable[..., Any]
RouteDecorator = Callable[[RequestHandler], RequestHandler]


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
    state: Any
    headers: Mapping[str, str]
    query_params: Mapping[str, str]
    path_params: MutableMapping[str, Any]
    client: Any
    url: Any

    def __init__(self, scope: Scope, receive: Receive, send: Send) -> None: ...


class APIRouter:
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


def Depends(dependency: Callable[..., Any] | None = ..., *, use_cache: bool = ...) -> Any: ...


__all__ = [
    "APIRouter",
    "Depends",
    "FastAPI",
    "HTTPException",
    "Request",
    "Response",
]
