from pytest_bdd import parsers, scenario, then, when

from autoresearch.config.models import ConfigModel
from autoresearch.search import Search


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
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    hybrid_results = Search.external_lookup(query, max_results=5)
    bdd_context["search_results"] = hybrid_results
    bdd_context["hybrid_results"] = hybrid_results
    cfg_sem = cfg.model_copy(deep=True)
    cfg_sem.search.hybrid_query = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg_sem)
    bdd_context["semantic_results"] = Search.external_lookup(query, max_results=5)
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)


@then("the search results should include vector results")
def check_vector_results(bdd_context):
    results = bdd_context["search_results"]
    assert any("embedding" in r for r in results)


@then("the first result should match the semantic search ordering")
def first_result_matches_semantic(bdd_context):
    hybrid = bdd_context["hybrid_results"][0]
    semantic = bdd_context["semantic_results"][0]
    assert hybrid["url"] == semantic["url"]


@then("the relevance scores should be normalized")
def relevance_scores_normalized(bdd_context):
    scores = [r["relevance_score"] for r in bdd_context["hybrid_results"]]
    assert all(0.0 <= s <= 1.0 for s in scores)
    assert scores == sorted(scores, reverse=True)
