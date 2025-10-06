# mypy: ignore-errors
import pytest

from autoresearch.search import Search
from autoresearch.typing.http import RequestsSessionProtocol


@pytest.mark.integration
def test_session_recovery_integration() -> None:
    """Search recreates HTTP session after closure."""
    session1: RequestsSessionProtocol = Search.get_http_session()
    Search.close_http_session()
    session2: RequestsSessionProtocol = Search.get_http_session()
    try:
        assert session1 is not session2
    finally:
        Search.close_http_session()
