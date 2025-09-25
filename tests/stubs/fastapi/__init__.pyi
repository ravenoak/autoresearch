from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Awaitable, Callable, Mapping, Sequence, TypeVar

from .responses import Response

T_Callable = TypeVar("T_Callable", bound=Callable[..., Any])


class _Client:
    host: str

    def __init__(self, host: str) -> None: ...


class Request:
    app: "FastAPI"
    client: _Client | None
    state: SimpleNamespace

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...


RequestResponseEndpoint = Callable[[Request], Awaitable[Response]]


def Depends(dependency: Callable[..., Awaitable[Any]] | Callable[..., Any]) -> Any: ...


class HTTPException(Exception):
    status_code: int
    detail: Any
    headers: Mapping[str, str] | None

    def __init__(
        self,
        status_code: int,
        *,
        detail: Any = ...,
        headers: Mapping[str, str] | None = ...,
    ) -> None: ...


class APIRouter:
    routes: list[Any]

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        methods: Sequence[str] | None = ...,
        **kwargs: Any,
    ) -> None: ...

    def include_router(self, router: "APIRouter", *args: Any, **kwargs: Any) -> None: ...

    def get(
        self, path: str, *args: Any, **kwargs: Any
    ) -> Callable[[T_Callable], T_Callable]: ...

    def post(
        self, path: str, *args: Any, **kwargs: Any
    ) -> Callable[[T_Callable], T_Callable]: ...

    def delete(
        self, path: str, *args: Any, **kwargs: Any
    ) -> Callable[[T_Callable], T_Callable]: ...


class FastAPI:
    router: APIRouter
    routes: list[Any]
    state: SimpleNamespace

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def add_middleware(
        self, middleware_class: type[Any], *args: Any, **kwargs: Any
    ) -> None: ...

    def include_router(self, router: APIRouter, *args: Any, **kwargs: Any) -> None: ...

    def add_exception_handler(
        self,
        exc_class: type[BaseException],
        handler: Callable[[Request, Exception], Response | Any],
    ) -> None: ...


__all__ = [
    "APIRouter",
    "Depends",
    "FastAPI",
    "HTTPException",
    "Request",
    "RequestResponseEndpoint",
]
