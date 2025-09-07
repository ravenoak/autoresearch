import pytest
from autoresearch.search.http import (
    close_http_session,
    get_http_session,
    set_http_session,
)


class DummySession:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:  # pragma: no cover - simple close
        self.closed = True


@pytest.mark.unit
def test_http_session_management(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify pooled HTTP session lifecycle helpers."""

    class DummyConfig:
        class search:
            http_pool_size = 1

    # First call should create a new session using configuration
    monkeypatch.setattr("autoresearch.search.http.get_config", lambda: DummyConfig())
    sess1 = get_http_session()
    assert sess1 is get_http_session()

    # Inject custom session and ensure it is returned
    custom = DummySession()
    set_http_session(custom)  # type: ignore[arg-type]
    assert get_http_session() is custom

    # Closing should reset global session
    close_http_session()
    assert custom.closed
    assert get_http_session() is not custom


@pytest.mark.requires_distributed
def test_set_http_session_registers_atexit(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    monkeypatch.setattr("autoresearch.search.http.atexit.register", lambda func: calls.append(func))
    close_http_session()
    custom = DummySession()
    set_http_session(custom)  # type: ignore[arg-type]
    assert get_http_session() is custom
    assert calls == [close_http_session]
    close_http_session()
    close_http_session()
