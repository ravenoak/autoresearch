import pytest
import requests

from autoresearch.search import Search
from autoresearch.config import ConfigModel
from autoresearch.errors import TimeoutError


def test_external_lookup_timeout_integration(monkeypatch):
    """Verify timeout exceptions propagate through integration layer."""
    def timeout_backend(query, max_results=5):
        raise requests.exceptions.Timeout("slow")

    monkeypatch.setitem(Search.backends, "timeout", timeout_backend)
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["timeout"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    with pytest.raises(TimeoutError):
        Search.external_lookup("q")
