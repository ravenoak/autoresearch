# mypy: ignore-errors
from autoresearch.search import Search


def test_reset_clears_state_and_session():
    session1 = Search.get_http_session()
    Search.backends["dummy"] = lambda q, max_results: []
    Search._shared_sentence_transformer = object()
    Search.reset()
    assert "dummy" not in Search.backends
    assert Search._shared_sentence_transformer is None
    session2 = Search.get_http_session()
    assert session1 is not session2
