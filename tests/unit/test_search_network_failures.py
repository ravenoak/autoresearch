import pytest
import requests

from autoresearch.search import Search
from autoresearch.config.models import ConfigModel
from autoresearch.errors import SearchError, TimeoutError


def test_external_lookup_request_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Search.external_lookup raises SearchError on network failure."""
    def failing_backend(query, max_results=5):
        raise requests.exceptions.RequestException("boom")

    monkeypatch.setitem(Search.backends, "fail", failing_backend)
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["fail"]
    cfg.search.context_aware.enabled = False
    import autoresearch.search.core as search_core
    monkeypatch.setattr(search_core, "get_config", lambda: cfg)

    with pytest.raises(SearchError) as excinfo:
        Search.external_lookup("q")

    assert "fail search failed" in str(excinfo.value)


def test_external_lookup_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Timeout errors propagate as TimeoutError."""
    def timeout_backend(query, max_results=5):
        raise requests.exceptions.Timeout("slow")

    monkeypatch.setitem(Search.backends, "timeout", timeout_backend)
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["timeout"]
    cfg.search.context_aware.enabled = False
    import autoresearch.search.core as search_core
    monkeypatch.setattr(search_core, "get_config", lambda: cfg)

    with pytest.raises(TimeoutError):
        Search.external_lookup("q")
