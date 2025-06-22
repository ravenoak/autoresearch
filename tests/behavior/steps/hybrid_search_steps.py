from pytest_bdd import scenario, when, then, parsers

from autoresearch.search import Search
from autoresearch.config import ConfigModel


@scenario("../features/hybrid_search.feature", "Combine keyword and vector results")
def test_hybrid_search():
    """Hybrid search mixes vector and keyword results."""
    pass


@when(parsers.parse('I perform a hybrid search for "{query}"'))
def perform_hybrid_search(query, monkeypatch, bdd_context):
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["local_file"]
    cfg.search.embedding_backends = ["duckdb"]
    cfg.search.hybrid_query = True
    cfg.search.context_aware.enabled = False
    docs_dir = bdd_context["docs_dir"]
    cfg.search.local_file.path = str(docs_dir)
    cfg.search.local_file.file_types = ["txt"]
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)
    bdd_context["search_results"] = Search.external_lookup(query, max_results=5)


@then("the search results should include vector results")
def check_vector_results(bdd_context):
    results = bdd_context["search_results"]
    assert any("embedding" in r for r in results)
