import responses
from responses import matchers
from autoresearch.config import ConfigModel

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
