from autoresearch.config import ConfigModel, SearchConfig
from autoresearch.config.loader import ConfigLoader
from autoresearch.search.core import Search


def _config(monkeypatch) -> None:
    cfg = ConfigModel(
        search=SearchConfig(
            bm25_weight=0.0,
            semantic_similarity_weight=1.0,
            source_credibility_weight=0.0,
            use_bm25=False,
            use_source_credibility=False,
            use_semantic_similarity=True,
        )
    )
    ConfigLoader.reset_instance()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)


def test_semantic_scores_ignore_zero_vectors(monkeypatch) -> None:
    _config(monkeypatch)
    results = [{"title": "a", "similarity": 0.0}, {"title": "b", "similarity": 0.0}]
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda self, q, docs, query_embedding=None: [0.9, 0.1],
    )
    ranked = Search.rank_results("q", results)
    assert [r["title"] for r in ranked] == ["a", "b"]
    assert ranked[0]["relevance_score"] == 1.0
    assert ranked[1]["relevance_score"] < 0.2
