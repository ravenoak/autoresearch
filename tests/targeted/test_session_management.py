"""Coverage for HTTP session utilities."""

from __future__ import annotations

from typing import Any, cast

import pytest

from tests.helpers.modules import ensure_stub_module
from tests.typing_helpers import make_config_model

ensure_stub_module(
    "pydantic_settings",
    {
        "BaseSettings": object,
        "CliApp": object,
        "SettingsConfigDict": dict,
    },
)
ensure_stub_module("docx", {"Document": object})

from autoresearch.typing.http import (  # noqa: E402
    RequestsAdapterProtocol,
    RequestsResponseProtocol,
    RequestsSessionProtocol,
)
import autoresearch.search.http as http  # noqa: E402


class DummyResponse:
    def __init__(self) -> None:
        self.raise_called = False
        self._headers: dict[str, str] = {}
        self.status_code = 200

    def raise_for_status(self) -> None:
        self.raise_called = True

    def json(self, **_: Any) -> dict[str, str]:
        return {"ok": "true"}

    @property
    def headers(self) -> dict[str, str]:
        return self._headers


class DummyAdapter:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class DummySession:
    def __init__(self) -> None:
        self.mounted: list[tuple[str, RequestsAdapterProtocol]] = []
        self.closed = False
        self.requests: list[tuple[str, str]] = []
        self._headers: dict[str, str] = {}
        self._adapters: list[tuple[str, RequestsAdapterProtocol]] = []
        self._default_adapter: RequestsAdapterProtocol = DummyAdapter()

    def request(
        self, method: str, url: str, *args: Any, **kwargs: Any
    ) -> RequestsResponseProtocol:
        self.requests.append((method, url))
        return DummyResponse()

    def mount(self, prefix: str, adapter: RequestsAdapterProtocol) -> None:
        self.mounted.append((prefix, adapter))
        self._adapters.append((prefix, adapter))

    def get_adapter(self, url: str) -> RequestsAdapterProtocol:
        for prefix, adapter in reversed(self._adapters):
            if url.startswith(prefix):
                return adapter
        return self._adapters[-1][1] if self._adapters else self._default_adapter

    def close(self) -> None:
        self.closed = True

    @property
    def headers(self) -> dict[str, str]:
        return self._headers

    def get(
        self, url: str, *args: Any, **kwargs: Any
    ) -> RequestsResponseProtocol:
        return self.request("GET", url, *args, **kwargs)

    def post(
        self, url: str, *args: Any, **kwargs: Any
    ) -> RequestsResponseProtocol:
        return self.request("POST", url, *args, **kwargs)


def test_get_http_session_creates_and_reuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """New session is created once and reused."""
    cfg = make_config_model(search_overrides={"http_pool_size": 3})
    monkeypatch.setattr(http, "get_config", lambda: cfg)
    requests_module = cast(Any, getattr(http, "requests"))
    monkeypatch.setattr(requests_module.adapters, "HTTPAdapter", lambda **k: DummyAdapter())
    monkeypatch.setattr(requests_module, "Session", DummySession)
    calls: list[object] = []
    atexit_mod = cast(Any, getattr(http, "atexit"))
    monkeypatch.setattr(atexit_mod, "register", lambda f: calls.append(f))
    http.close_http_session()

    first = http.get_http_session()
    second = http.get_http_session()

    assert isinstance(first, DummySession)
    assert isinstance(first, RequestsSessionProtocol)
    assert first is second
    assert calls == [http.close_http_session]
    assert [prefix for prefix, _ in first.mounted] == ["http://", "https://"]
    http.close_http_session()


def test_set_and_close_http_session(monkeypatch: pytest.MonkeyPatch) -> None:
    """Injected session registers atexit and closes cleanly."""
    dummy = DummySession()
    calls: list[object] = []
    atexit_mod = cast(Any, getattr(http, "atexit"))
    monkeypatch.setattr(atexit_mod, "register", lambda f: calls.append(f))
    http.set_http_session(dummy)

    retrieved = http.get_http_session()
    assert isinstance(retrieved, DummySession)
    assert retrieved is dummy
    assert calls == [http.close_http_session]

    http.close_http_session()
    assert dummy.closed is True
    assert http._http_session is None


def test_protocol_request_usage() -> None:
    """Dummy session satisfies the protocol and returns responses."""

    session = DummySession()
    assert isinstance(session, RequestsSessionProtocol)

    response = session.get("https://example.com")
    assert isinstance(response, DummyResponse)
    assert response.raise_called is False
    response.raise_for_status()
    assert response.raise_called is True


def test_protocol_headers_are_mutable() -> None:
    """Sessions expose mutable headers consistent with the protocol."""

    session = DummySession()
    session.headers["User-Agent"] = "autoresearch-tests"

    assert session.headers["User-Agent"] == "autoresearch-tests"


def test_adapter_protocol_supports_close() -> None:
    """Adapters satisfying the protocol can be mounted and closed."""

    session = DummySession()
    adapter = DummyAdapter()

    assert isinstance(adapter, RequestsAdapterProtocol)

    session.mount("http://", adapter)
    assert session.mounted == [("http://", adapter)]

    adapter.close()
    assert adapter.closed is True
