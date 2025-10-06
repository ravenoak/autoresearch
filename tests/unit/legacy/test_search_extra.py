# mypy: ignore-errors
import json
import sys

import pytest

from tests.helpers.modules import ensure_stub_module

# Provide dummy optional modules before importing Search
ensure_stub_module("kuzu")
ensure_stub_module("spacy.cli", {"download": lambda *_: None})
ensure_stub_module("spacy", {"load": lambda *_: None})
ensure_stub_module("bertopic")
ensure_stub_module(
    "fastembed",
    {
        "OnnxTextEmbedding": lambda *_: None,
        "TextEmbedding": lambda *_: None,
    },
)

from autoresearch.search import (  # noqa: E402
    Search,
    get_http_session,
    close_http_session,
)
from autoresearch.config.models import ConfigModel  # noqa: E402
from autoresearch.errors import SearchError  # noqa: E402


def test_unknown_backend_raises(monkeypatch):
    with Search.temporary_state() as search:
        search.backends = {}
        cfg = ConfigModel(loops=1)
        cfg.search.backends = ["missing"]
        cfg.search.context_aware.enabled = False
        monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
        with pytest.raises(SearchError):
            search.external_lookup("q")


def test_backend_json_error(monkeypatch):
    def bad_backend(query, max_results=5):
        raise json.JSONDecodeError("bad", "", 0)

    with Search.temporary_state() as search:
        search.backends = {"bad": bad_backend}
        cfg = ConfigModel(loops=1)
        cfg.search.backends = ["bad"]
        cfg.search.context_aware.enabled = False
        monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
        was = sys.modules.pop("pytest")
        try:
            with pytest.raises(SearchError):
                search.external_lookup("q")
        finally:
            sys.modules["pytest"] = was


def test_http_session_reuse():
    close_http_session()
    s1 = get_http_session()
    s2 = get_http_session()
    assert s1 is s2
    close_http_session()
    assert get_http_session() is not s1
