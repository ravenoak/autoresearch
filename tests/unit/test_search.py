import responses
from responses import matchers

from autoresearch.search import Search


@responses.activate
def test_external_lookup():
    query = "python"
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_redirect": "1", "no_html": "1"}
    responses.add(
        responses.GET,
        url,
        match=[matchers.query_param_matcher(params)],
        json={"RelatedTopics": [{"Text": "Python", "FirstURL": "https://python.org"}]},
    )
    results = Search.external_lookup(query, max_results=1)
    assert results == [{"title": "Python", "url": "https://python.org"}]


@responses.activate
def test_external_lookup_special_chars():
    query = "C++ tutorial & basics"
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_redirect": "1", "no_html": "1"}
    responses.add(
        responses.GET,
        url,
        match=[matchers.query_param_matcher(params)],
        json={"RelatedTopics": [{"Text": "C++", "FirstURL": "https://cplusplus.com"}]},
    )
    results = Search.external_lookup(query, max_results=1)
    assert results == [{"title": "C++", "url": "https://cplusplus.com"}]


def test_generate_queries():
    assert Search.generate_queries("q") == ["q"]
