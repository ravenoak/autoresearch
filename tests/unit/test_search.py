import json
import responses
from responses import matchers
import pytest
import requests
from autoresearch.config import ConfigModel
from autoresearch.errors import SearchError, TimeoutError

from autoresearch.search import Search


@responses.activate
def test_external_lookup(monkeypatch):
    cfg = ConfigModel(search_backends=["duckduckgo"], loops=1)
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)
    query = "python"
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_redirect": "1", "no_html": "1"}
    responses.add(
        responses.GET,
        url,
        match=[matchers.query_param_matcher(params)],
        json={
            "RelatedTopics": [
                {"Text": "Python", "FirstURL": "https://python.org"}
            ]
        },
    )
    results = Search.external_lookup(query, max_results=1)
    assert results == [{"title": "Python", "url": "https://python.org"}]


@responses.activate
def test_external_lookup_special_chars(monkeypatch):
    cfg = ConfigModel(search_backends=["duckduckgo"], loops=1)
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)
    query = "C++ tutorial & basics"
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_redirect": "1", "no_html": "1"}
    responses.add(
        responses.GET,
        url,
        match=[matchers.query_param_matcher(params)],
        json={
            "RelatedTopics": [
                {"Text": "C++", "FirstURL": "https://cplusplus.com"}
            ]
        },
    )
    results = Search.external_lookup(query, max_results=1)
    assert results == [{"title": "C++", "url": "https://cplusplus.com"}]


def test_generate_queries():
    queries = Search.generate_queries("some topic")
    assert "some topic" in queries
    assert any(q.startswith("What is") for q in queries)
    assert len(queries) >= 2

    emb = Search.generate_queries("abc", return_embeddings=True)
    assert isinstance(emb, list)
    assert all(isinstance(v, float) for v in emb)


@responses.activate
def test_external_lookup_backend_error(monkeypatch):
    """Test that a SearchError is raised when a search backend fails."""
    cfg = ConfigModel(search_backends=["duckduckgo"], loops=1)
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)
    query = "python"
    url = "https://api.duckduckgo.com/"

    # Mock a failed HTTP request
    responses.add(
        responses.GET,
        url,
        status=500,  # Server error
        json={"error": "Internal Server Error"}
    )

    # The external_lookup method should raise a SearchError
    with pytest.raises(SearchError) as excinfo:
        Search.external_lookup(query, max_results=1)

    # Verify the error message and cause
    assert "search failed" in str(excinfo.value)
    assert excinfo.value.__cause__ is not None
    assert "backend" in excinfo.value.context
    assert excinfo.value.context["backend"] == "duckduckgo"


@responses.activate
def test_duckduckgo_timeout_error(monkeypatch):
    """Test that a TimeoutError is raised when DuckDuckGo search times out."""
    cfg = ConfigModel(search_backends=["duckduckgo"], loops=1)
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)
    query = "python"
    url = "https://api.duckduckgo.com/"

    # Mock a timeout
    responses.add(
        responses.GET,
        url,
        body=requests.exceptions.Timeout("Connection timed out")
    )

    # The external_lookup method should raise a TimeoutError
    with pytest.raises(TimeoutError) as excinfo:
        Search.external_lookup(query, max_results=1)

    # Verify the error message and cause
    assert "timed out" in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, requests.exceptions.Timeout)
    assert "backend" in excinfo.value.context
    assert excinfo.value.context["backend"] == "duckduckgo"


@responses.activate
def test_duckduckgo_json_decode_error(monkeypatch):
    """Test that a SearchError is raised when DuckDuckGo returns invalid JSON."""
    cfg = ConfigModel(search_backends=["duckduckgo"], loops=1)
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)
    query = "python"
    url = "https://api.duckduckgo.com/"

    # Mock an invalid JSON response
    responses.add(
        responses.GET,
        url,
        body="Invalid JSON",
        content_type="application/json"
    )

    # The external_lookup method should raise a SearchError
    with pytest.raises(SearchError) as excinfo:
        Search.external_lookup(query, max_results=1)

    # Verify the error message and cause
    assert "search failed" in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, json.JSONDecodeError)
    assert "backend" in excinfo.value.context
    assert excinfo.value.context["backend"] == "duckduckgo"


@responses.activate
def test_serper_backend_error(monkeypatch):
    """Test that a SearchError is raised when Serper search fails."""
    cfg = ConfigModel(search_backends=["serper"], loops=1)
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)
    monkeypatch.setenv("SERPER_API_KEY", "test_key")
    query = "python"
    url = "https://google.serper.dev/search"

    # Mock a failed HTTP request
    responses.add(
        responses.POST,
        url,
        status=403,  # Forbidden (e.g., invalid API key)
        json={"error": "Invalid API key"}
    )

    # The external_lookup method should raise a SearchError
    with pytest.raises(SearchError) as excinfo:
        Search.external_lookup(query, max_results=1)

    # Verify the error message and cause
    assert "search failed" in str(excinfo.value)
    assert excinfo.value.__cause__ is not None
    assert "backend" in excinfo.value.context
    assert excinfo.value.context["backend"] == "serper"


@responses.activate
def test_serper_timeout_error(monkeypatch):
    """Test that a TimeoutError is raised when Serper search times out."""
    cfg = ConfigModel(search_backends=["serper"], loops=1)
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)
    monkeypatch.setenv("SERPER_API_KEY", "test_key")
    query = "python"
    url = "https://google.serper.dev/search"

    # Mock a timeout
    responses.add(
        responses.POST,
        url,
        body=requests.exceptions.Timeout("Connection timed out")
    )

    # The external_lookup method should raise a TimeoutError
    with pytest.raises(TimeoutError) as excinfo:
        Search.external_lookup(query, max_results=1)

    # Verify the error message and cause
    assert "timed out" in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, requests.exceptions.Timeout)
    assert "backend" in excinfo.value.context
    assert excinfo.value.context["backend"] == "serper"
