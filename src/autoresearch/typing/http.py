"""Protocols describing the subset of the ``requests`` API that we rely on."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class RequestsResponseProtocol(Protocol):
    """Structural type for ``requests.Response`` objects."""

    status_code: int

    @property
    def headers(self) -> Mapping[str, str]:
        """Return HTTP headers associated with the response."""

    def json(self, **kwargs: Any) -> Any:
        """Return a decoded JSON payload."""

    def raise_for_status(self) -> None:
        """Raise an HTTPError if the response status indicates failure."""


@runtime_checkable
class RequestsSessionProtocol(Protocol):
    """Structural type for ``requests.Session`` objects."""

    @property
    def headers(self) -> Mapping[str, str]:
        """Return default headers sent with each request."""

    def mount(self, prefix: str, adapter: Any) -> None:
        """Register an adapter that handles the given URL prefix."""

    def close(self) -> None:
        """Release any pooled network resources."""

    def request(
        self, method: str, url: str, *args: Any, **kwargs: Any
    ) -> RequestsResponseProtocol:
        """Issue an HTTP request with the provided method and URL."""

    def get(self, url: str, *args: Any, **kwargs: Any) -> RequestsResponseProtocol:
        """Issue a GET request."""

    def post(self, url: str, *args: Any, **kwargs: Any) -> RequestsResponseProtocol:
        """Issue a POST request."""
