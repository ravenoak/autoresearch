from __future__ import annotations

from typing import Any, Mapping, MutableMapping

from . import exceptions
from .adapters import BaseAdapter, HTTPAdapter


class Response:
    status_code: int
    text: str

    def __init__(self, *, status_code: int = 200, text: str = "", content: Any = ...) -> None: ...

    def json(self, **kwargs: Any) -> Any: ...

    def raise_for_status(self) -> None: ...

    @property
    def headers(self) -> Mapping[str, str]: ...


class Session:
    def __init__(self) -> None: ...

    def get(self, url: str, *args: Any, **kwargs: Any) -> Response: ...

    def post(self, url: str, *args: Any, **kwargs: Any) -> Response: ...

    def request(self, method: str, url: str, *args: Any, **kwargs: Any) -> Response: ...

    def close(self) -> None: ...

    def mount(self, prefix: str, adapter: BaseAdapter) -> None: ...

    @property
    def headers(self) -> MutableMapping[str, str]: ...


def get(url: str, *args: Any, **kwargs: Any) -> Response: ...


def post(url: str, *args: Any, **kwargs: Any) -> Response: ...


def request(method: str, url: str, *args: Any, **kwargs: Any) -> Response: ...


RequestException = exceptions.RequestException
Timeout = exceptions.Timeout

__all__ = [
    "HTTPAdapter",
    "BaseAdapter",
    "RequestException",
    "Response",
    "Session",
    "Timeout",
    "exceptions",
    "get",
    "post",
    "request",
]
