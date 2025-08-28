"""Coverage for HTTP session utilities."""

import sys
from types import SimpleNamespace

sys.modules.setdefault(
    "pydantic_settings",
    SimpleNamespace(BaseSettings=object, CliApp=object, SettingsConfigDict=dict),
)
sys.modules.setdefault("docx", SimpleNamespace(Document=object))

import autoresearch.search.http as http  # noqa: E402


class DummySession:
    def __init__(self) -> None:
        self.mounted = []
        self.closed = False

    def mount(self, prefix, adapter) -> None:
        self.mounted.append((prefix, adapter))

    def close(self) -> None:
        self.closed = True


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
    assert first is second
    assert calls == [http.close_http_session]

    http.close_http_session()


def test_set_and_close_http_session(monkeypatch):
    """Injected session registers atexit and closes cleanly."""
    dummy = DummySession()
    calls = []
    monkeypatch.setattr(http.atexit, "register", lambda f: calls.append(f))
    http.set_http_session(dummy)

    assert http.get_http_session() is dummy
    assert calls == [http.close_http_session]

    http.close_http_session()
    assert dummy.closed
    assert http._http_session is None
