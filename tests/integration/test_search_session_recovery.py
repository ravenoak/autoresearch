import pytest

from autoresearch.search import Search


@pytest.mark.integration
def test_session_recovery_integration() -> None:
    """Search recreates HTTP session after closure."""
    session1 = Search.get_http_session()
    Search.close_http_session()
    session2 = Search.get_http_session()
    try:
        assert session1 is not session2
    finally:
        Search.close_http_session()
