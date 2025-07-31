import sys
import json
import types
import pytest

# Provide dummy optional modules before importing Search
sys.modules.setdefault("kuzu", types.SimpleNamespace())
sys.modules.setdefault("spacy", types.SimpleNamespace(load=lambda *_: None, cli=types.SimpleNamespace(download=lambda *_: None)))
sys.modules.setdefault("bertopic", types.SimpleNamespace())
sys.modules.setdefault(
    "sentence_transformers",
    types.SimpleNamespace(SentenceTransformer=lambda *_: None),
)

from autoresearch.search import (  # noqa: E402
    Search,
    get_http_session,
    close_http_session,
)
from autoresearch.config.models import ConfigModel  # noqa: E402
from autoresearch.errors import SearchError  # noqa: E402


def test_unknown_backend_raises(monkeypatch):
    Search.backends = {}
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["missing"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    was = sys.modules.pop('pytest')
    try:
        with pytest.raises(SearchError):
            Search.external_lookup("q")
    finally:
        sys.modules['pytest'] = was


def test_backend_json_error(monkeypatch):
    def bad_backend(query, max_results=5):
        raise json.JSONDecodeError("bad", "", 0)

    Search.backends = {"bad": bad_backend}
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["bad"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    was = sys.modules.pop('pytest')
    try:
        with pytest.raises(SearchError):
            Search.external_lookup("q")
    finally:
        sys.modules['pytest'] = was


def test_http_session_reuse():
    close_http_session()
    s1 = get_http_session()
    s2 = get_http_session()
    assert s1 is s2
    close_http_session()
    assert get_http_session() is not s1
