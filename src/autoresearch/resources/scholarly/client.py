"""Shared HTTP client utilities for scholarly providers."""

from __future__ import annotations

import json
import threading
from typing import Iterator

import httpx

_USER_AGENT = "Autoresearch-ScholarlyFetcher/1.0"
_TIMEOUT = httpx.Timeout(10.0, connect=5.0, read=10.0)
_LOCK = threading.RLock()
_CLIENT: httpx.Client | None = None


def get_http_client() -> httpx.Client:
    """Return a process-wide shared :class:`httpx.Client`."""

    global _CLIENT
    with _LOCK:
        if _CLIENT is None:
            _CLIENT = httpx.Client(headers={"User-Agent": _USER_AGENT}, timeout=_TIMEOUT)
        return _CLIENT


def iter_json_lines(response: httpx.Response) -> Iterator[dict[str, object]]:
    """Yield JSON objects from a newline-delimited JSON response."""

    for raw_line in response.text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        yield json.loads(line)


def reset_http_client() -> None:
    """Dispose of the shared HTTP client (used by tests)."""

    global _CLIENT
    with _LOCK:
        if _CLIENT is not None:
            _CLIENT.close()
            _CLIENT = None


__all__ = ["get_http_client", "reset_http_client", "iter_json_lines"]
