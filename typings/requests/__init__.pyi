from __future__ import annotations

from typing import Any, Mapping, MutableMapping, overload


class RequestException(Exception): ...


class Response:
    status_code: int
    headers: Mapping[str, str]
    text: str

    def json(self) -> Any: ...


class Session:
    headers: MutableMapping[str, str]

    def get(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = ...,
        headers: Mapping[str, str] | None = ...,
        timeout: float | tuple[float, float] | None = ...,
    ) -> Response: ...

    def post(
        self,
        url: str,
        *,
        json: Any = ...,
        data: Any = ...,
        headers: Mapping[str, str] | None = ...,
        timeout: float | tuple[float, float] | None = ...,
    ) -> Response: ...

    def close(self) -> None: ...


def get(
    url: str,
    *,
    params: Mapping[str, Any] | None = ...,
    headers: Mapping[str, str] | None = ...,
    timeout: float | tuple[float, float] | None = ...,
) -> Response: ...


def post(
    url: str,
    *,
    json: Any = ...,
    data: Any = ...,
    headers: Mapping[str, str] | None = ...,
    timeout: float | tuple[float, float] | None = ...,
) -> Response: ...


__all__ = ["RequestException", "Response", "Session", "get", "post"]
