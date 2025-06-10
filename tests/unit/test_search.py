import responses

from autoresearch.search import Search


@responses.activate
def test_external_lookup():
    query = "python"
    url = f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1&no_html=1"
    responses.add(responses.GET, url, json={"RelatedTopics": [{"Text": "Python", "FirstURL": "https://python.org"}]})
    results = Search.external_lookup(query, max_results=1)
    assert results == [{"title": "Python", "url": "https://python.org"}]


def test_generate_queries():
    assert Search.generate_queries("q") == ["q"]
