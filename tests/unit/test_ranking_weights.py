from __future__ import annotations

import pytest

from autoresearch.search import Search
from autoresearch.config.models import ConfigModel, SearchConfig
from autoresearch.config.loader import ConfigLoader
from autoresearch.errors import ConfigError


def test_search_config_weight_validation() -> None:
    """Validate that weights either sum to 1 or raise ``ConfigError``."""
    valid = [(0.5, 0.3, 0.2), (0.0, 0.0, 1.0)]
    invalid = [(0.2, 0.2, 0.2), (0.4, 0.4, 0.3)]
    for w1, w2, w3 in valid:
        cfg = SearchConfig(
            bm25_weight=w1,
            semantic_similarity_weight=w2,
            source_credibility_weight=w3,
        )
        assert pytest.approx(
            cfg.bm25_weight
            + cfg.semantic_similarity_weight
            + cfg.source_credibility_weight,
            0.001,
        ) == 1.0
    for w1, w2, w3 in invalid:
        with pytest.raises(ConfigError):
            SearchConfig(
                bm25_weight=w1,
                semantic_similarity_weight=w2,
                source_credibility_weight=w3,
            )


def test_default_config_weights_sum_to_one(config_loader) -> None:
    """Ensure default configuration loads with normalized ranking weights."""
    cfg = config_loader.load_config()
    total = (
        cfg.search.semantic_similarity_weight
        + cfg.search.bm25_weight
        + cfg.search.source_credibility_weight
    )
    assert pytest.approx(total, abs=0.001) == 1.0


def _setup_search(monkeypatch, w1: float, w2: float, w3: float) -> None:
    cfg = ConfigModel(
        search=SearchConfig(
            bm25_weight=w1,
            semantic_similarity_weight=w2,
            source_credibility_weight=w3,
        )
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None
    monkeypatch.setattr(
        Search, "calculate_bm25_scores", staticmethod(lambda q, r: [1.0] * len(r))
    )
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda self, q, r, query_embedding=None: [1.0] * len(r),
    )
    monkeypatch.setattr(
        Search, "assess_source_credibility", lambda self, r: [1.0] * len(r)
    )
    cfg.search.use_semantic_similarity = False


def test_rank_results_sorted(monkeypatch):
    results = [
        {"title": "a", "url": "https://example.com/a"},
        {"title": "b", "url": "https://example.com/b"},
    ]
    _setup_search(monkeypatch, 0.2, 0.3, 0.5)
    ranked = Search.rank_results("q", results)
    scores = [r["relevance_score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)


def test_cross_backend_rank_sorted(monkeypatch):
    backend_results = {
        "b1": [{"title": "a", "url": "https://example.com/a"}],
        "b2": [{"title": "b", "url": "https://example.com/b"}],
    }
    _setup_search(monkeypatch, 0.3, 0.3, 0.4)
    ranked = Search.cross_backend_rank("q", backend_results)
    scores = [r["relevance_score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)


def test_rank_results_invalid_sum(monkeypatch):
    results = [
        {"title": "a", "url": "https://example.com/a"},
        {"title": "b", "url": "https://example.com/b"},
    ]
    cfg = ConfigModel.model_construct(
        search=SearchConfig.model_construct(
            bm25_weight=0.2,
            semantic_similarity_weight=0.3,
            source_credibility_weight=0.4,
        )
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None
    monkeypatch.setattr(
        Search, "calculate_bm25_scores", staticmethod(lambda q, r: [1.0] * len(r))
    )
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda self, q, r, query_embedding=None: [1.0] * len(r),
    )
    monkeypatch.setattr(
        Search, "assess_source_credibility", lambda self, r: [1.0] * len(r)
    )
    with pytest.raises(ConfigError):
        Search.rank_results("q", results)
