from __future__ import annotations

import pytest

from autoresearch.search import Search
from autoresearch.search import http as search_http

pytestmark = [pytest.mark.unit]


def test_http_session_retries_and_reuse() -> None:
    """HTTP session uses pooling and retry configuration."""
    session1 = Search.get_http_session()
    session2 = Search.get_http_session()
    assert session1 is session2
    adapter = session1.get_adapter("https://")
    retries = getattr(adapter, "max_retries", None)
    assert retries is not None
    assert getattr(retries, "total", 0) >= 3
    Search.close_http_session()


def test_http_session_recovery() -> None:
    """A new session is created after the previous one is closed."""
    session1 = Search.get_http_session()
    Search.close_http_session()
    session2 = Search.get_http_session()
    try:
        assert session1 is not session2
    finally:
        Search.close_http_session()


def test_http_session_adapter_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adapter construction failures do not leak sessions or registrations."""

    Search.close_http_session()

    def boom(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("adapter failure")

    monkeypatch.setattr(search_http, "_build_search_adapter", boom)

    with pytest.raises(RuntimeError, match="adapter failure"):
        Search.get_http_session()

    assert search_http._http_session is None
    assert search_http._atexit_registered is False
