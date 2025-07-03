import types
import pytest
from autoresearch import search
from autoresearch.errors import ConfigError


def test_bm25_fallback(monkeypatch):
    monkeypatch.setattr(search, "BM25_AVAILABLE", False)
    scores = search.Search.calculate_bm25_scores("q", [{"title": "t"}])
    assert scores == [1.0]


def test_assess_source_credibility():
    scores = search.Search.assess_source_credibility([
        {"url": "https://wikipedia.org/Article"},
        {"url": "https://unknown.domain"},
    ])
    assert scores[0] > scores[1]


def test_rank_results_weight_error(monkeypatch):
    class SCfg:
        bm25_weight = 0.6
        semantic_similarity_weight = 0.3
        source_credibility_weight = 0.3
        use_bm25 = True
        use_semantic_similarity = True
        use_source_credibility = True

    cfg = types.SimpleNamespace(search=SCfg())
    monkeypatch.setattr(search, "get_config", lambda: cfg)
    with pytest.raises(ConfigError):
        search.Search.rank_results("q", [{"title": "t", "url": "u"}])
