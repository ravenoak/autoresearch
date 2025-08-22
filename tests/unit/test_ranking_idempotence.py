from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, SearchConfig
from autoresearch.search.core import Search


def _setup(monkeypatch) -> None:
    cfg = ConfigModel(
        search=SearchConfig(
            bm25_weight=0.5,
            semantic_similarity_weight=0.3,
            source_credibility_weight=0.2,
        )
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None
    monkeypatch.setattr(Search, "calculate_bm25_scores", staticmethod(lambda q, r: [0.2, 0.1]))
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda self, q, r, query_embedding=None: [0.3, 0.4],
    )
    monkeypatch.setattr(Search, "assess_source_credibility", lambda self, r: [0.5, 0.6])


def test_rank_results_idempotent(monkeypatch) -> None:
    """Ranking a sorted list again leaves the order unchanged."""
    results = [
        {"title": "a", "url": "https://a"},
        {"title": "b", "url": "https://b"},
    ]
    _setup(monkeypatch)
    ranked = Search.rank_results("q", results)
    reranked = Search.rank_results("q", ranked)
    assert [r["url"] for r in ranked] == [r["url"] for r in reranked]
