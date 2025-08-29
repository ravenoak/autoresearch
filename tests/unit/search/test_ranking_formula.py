import pytest

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, SearchConfig
from autoresearch.errors import ConfigError
from autoresearch.search import Search


def test_rank_results_weighted_combination(monkeypatch: pytest.MonkeyPatch) -> None:
    """Search.rank_results combines scores using configured weights."""
    docs = [
        {"title": "A", "url": "https://a", "similarity": 0.4},
        {"title": "B", "url": "https://b", "similarity": 0.1},
    ]
    bm25 = [0.2, 0.5]
    semantic = [0.4, 0.1]
    credibility = [0.3, 0.7]
    cfg = ConfigModel(
        search=SearchConfig(
            bm25_weight=0.3,
            semantic_similarity_weight=0.4,
            source_credibility_weight=0.3,
            use_bm25=True,
            use_semantic_similarity=True,
            use_source_credibility=True,
        )
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None
    monkeypatch.setattr(Search, "calculate_bm25_scores", staticmethod(lambda q, r: bm25))
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda self, q, r, query_embedding=None: semantic,
    )
    monkeypatch.setattr(Search, "assess_source_credibility", lambda self, r: credibility)

    ranked = Search.rank_results("q", docs)
    scores = []
    for i in range(len(docs)):
        merged = bm25[i] * 0.3 + semantic[i] * 0.4
        scores.append(merged + credibility[i] * 0.3)
    assert [r["title"] for r in ranked] == ["B", "A"]
    assert [r["relevance_score"] for r in ranked] == pytest.approx(sorted(scores, reverse=True))


def test_rank_results_invalid_weights(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid weight sums raise ConfigError."""
    cfg = ConfigModel(
        search=SearchConfig(
            bm25_weight=0.3,
            semantic_similarity_weight=0.4,
            source_credibility_weight=0.3,
            use_bm25=True,
            use_semantic_similarity=True,
            use_source_credibility=True,
        )
    )
    cfg.search.bm25_weight = 0.6
    cfg.search.semantic_similarity_weight = 0.3
    cfg.search.source_credibility_weight = 0.2
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None
    monkeypatch.setattr(Search, "calculate_bm25_scores", staticmethod(lambda q, r: [1.0]))
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda self, q, r, query_embedding=None: [1.0],
    )
    monkeypatch.setattr(Search, "assess_source_credibility", lambda self, r: [1.0])
    with pytest.raises(ConfigError):
        Search.rank_results("q", [{"url": "https://a"}])
