from __future__ import annotations

from typing import Any, Mapping

from . import FastAPI
from .responses import Response


class TestClient:
    app: FastAPI

    def __init__(self, app: Any, base_url: str | None = ..., **kwargs: Any) -> None: ...

    def get(self, url: str, *, params: Mapping[str, Any] | None = ..., headers: Mapping[str, str] | None = ...) -> Response: ...

    def post(
        self,
        url: str,
        *,
        json: Any = ...,
        data: Any = ...,
        headers: Mapping[str, str] | None = ...,
    ) -> Response: ...

    def delete(self, url: str, *, headers: Mapping[str, str] | None = ...) -> Response: ...

    def put(
        self,
        url: str,
        *,
        json: Any = ...,
        headers: Mapping[str, str] | None = ...,
    ) -> Response: ...

    def __enter__(self) -> TestClient: ...

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: Any) -> None: ...


__all__ = ["TestClient"]
