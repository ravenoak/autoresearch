"""Coverage for HTTP session utilities."""

from types import SimpleNamespace

from tests.helpers.modules import ensure_stub_module

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

    def json(self) -> dict[str, str]:
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
        self.mounted: list[tuple[str, object]] = []
        self.closed = False
        self.requests: list[tuple[str, str]] = []
        self._headers: dict[str, str] = {}

    def request(self, method, url, **kwargs):
        self.requests.append((method, url))
        return DummyResponse()

    def mount(self, prefix, adapter: RequestsAdapterProtocol) -> None:
        self.mounted.append((prefix, adapter))

    def close(self) -> None:
        self.closed = True

    @property
    def headers(self) -> dict[str, str]:
        return self._headers

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)


def test_get_http_session_creates_and_reuses(monkeypatch):
    """New session is created once and reused."""
    cfg = SimpleNamespace(search=SimpleNamespace(http_pool_size=3))
    monkeypatch.setattr(http, "get_config", lambda: cfg)
    monkeypatch.setattr(http.requests.adapters, "HTTPAdapter", lambda **k: object())
    monkeypatch.setattr(http.requests, "Session", DummySession)
    calls = []
    monkeypatch.setattr(http.atexit, "register", lambda f: calls.append(f))
    http.close_http_session()

    first = http.get_http_session()
    second = http.get_http_session()

    assert isinstance(first, DummySession)
    assert isinstance(first, RequestsSessionProtocol)
    assert first is second
    assert calls == [http.close_http_session]
    assert [prefix for prefix, _ in first.mounted] == ["http://", "https://"]
    http.close_http_session()


def test_set_and_close_http_session(monkeypatch):
    """Injected session registers atexit and closes cleanly."""
    dummy = DummySession()
    calls = []
    monkeypatch.setattr(http.atexit, "register", lambda f: calls.append(f))
    http.set_http_session(dummy)

    assert http.get_http_session() is dummy
    assert isinstance(dummy, RequestsSessionProtocol)
    assert calls == [http.close_http_session]

    http.close_http_session()
    assert dummy.closed
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
