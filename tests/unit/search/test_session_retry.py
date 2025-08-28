from autoresearch.search import Search


def test_http_session_retries_and_reuse() -> None:
    """HTTP session uses pooling and retry configuration."""
    session1 = Search.get_http_session()
    session2 = Search.get_http_session()
    assert session1 is session2
    adapter = session1.get_adapter("https://")
    assert adapter.max_retries.total >= 3
    Search.close_http_session()
