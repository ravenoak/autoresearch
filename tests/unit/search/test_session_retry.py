import pytest

from autoresearch.search import Search

pytestmark = [pytest.mark.unit]


def test_http_session_retries_and_reuse() -> None:
    """HTTP session uses pooling and retry configuration."""
    session1 = Search.get_http_session()
    session2 = Search.get_http_session()
    assert session1 is session2
    adapter = session1.get_adapter("https://")
    assert adapter.max_retries.total >= 3
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
