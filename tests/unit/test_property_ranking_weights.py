from hypothesis import given, strategies as st
import pytest

from autoresearch.search import Search
from autoresearch.config.models import ConfigModel, SearchConfig
from autoresearch.config.loader import ConfigLoader
from autoresearch.errors import ConfigError


@pytest.mark.xfail(reason="Pending investigation of unhashable constants")
@given(
    w1=st.floats(min_value=0, max_value=1),
    w2=st.floats(min_value=0, max_value=1),
    w3=st.floats(min_value=0, max_value=1),
)
def test_search_config_weight_validation(w1, w2, w3):
    total = w1 + w2 + w3
    if abs(total - 1.0) <= 0.001:
        cfg = SearchConfig(
            bm25_weight=w1,
            semantic_similarity_weight=w2,
            source_credibility_weight=w3,
        )
        assert pytest.approx(cfg.bm25_weight + cfg.semantic_similarity_weight + cfg.source_credibility_weight, 0.001) == 1.0
    else:
        with pytest.raises(ConfigError):
            SearchConfig(
                bm25_weight=w1,
                semantic_similarity_weight=w2,
                source_credibility_weight=w3,
            )


@given(
    results=st.lists(
        st.fixed_dictionaries({"title": st.text(min_size=1), "url": st.just("https://example.com")}),
        min_size=1,
        max_size=5,
    ),
    weights=st.tuples(
        st.floats(min_value=0, max_value=1),
        st.floats(min_value=0, max_value=1),
        st.floats(min_value=0, max_value=1),
    ).filter(lambda t: sum(t) > 0),
)
def test_rank_results_sorted(monkeypatch, results, weights):
    w1, w2, w3 = weights
    total = w1 + w2 + w3
    cfg = ConfigModel(
        search=SearchConfig(
            bm25_weight=w1 / total,
            semantic_similarity_weight=w2 / total,
            source_credibility_weight=w3 / total,
        )
    )

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    monkeypatch.setattr(Search, "calculate_bm25_scores", lambda q, r: [1.0] * len(r))
    monkeypatch.setattr(Search, "calculate_semantic_similarity", lambda q, r, query_embedding=None: [1.0] * len(r))
    monkeypatch.setattr(Search, "assess_source_credibility", lambda r: [1.0] * len(r))

    ranked = Search.rank_results("q", results)
    scores = [res["relevance_score"] for res in ranked]
    assert scores == sorted(scores, reverse=True)


@given(
    results=st.lists(
        st.fixed_dictionaries({"title": st.text(min_size=1), "url": st.just("https://example.com")}),
        min_size=1,
        max_size=5,
    ),
    weights=st.tuples(
        st.floats(min_value=0, max_value=1),
        st.floats(min_value=0, max_value=1),
        st.floats(min_value=0, max_value=1),
    ).filter(lambda t: sum(t) > 0),
)
def test_rank_results_weight_sum_one(monkeypatch, results, weights):
    w1, w2, w3 = weights
    total = w1 + w2 + w3
    w1, w2, w3 = w1 / total, w2 / total, w3 / total
    cfg = ConfigModel(
        search=SearchConfig(
            bm25_weight=w1,
            semantic_similarity_weight=w2,
            source_credibility_weight=w3,
        )
    )

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    monkeypatch.setattr(Search, "calculate_bm25_scores", lambda q, r: [1.0] * len(r))
    monkeypatch.setattr(Search, "calculate_semantic_similarity", lambda q, r, query_embedding=None: [1.0] * len(r))
    monkeypatch.setattr(Search, "assess_source_credibility", lambda r: [1.0] * len(r))

    ranked = Search.rank_results("q", results)
    scores = [res["relevance_score"] for res in ranked]
    assert scores == sorted(scores, reverse=True)


@given(
    backend_results=st.dictionaries(
        st.text(min_size=1, max_size=5),
        st.lists(
            st.fixed_dictionaries(
                {"title": st.text(min_size=1), "url": st.just("https://example.com")}
            ),
            min_size=1,
            max_size=3,
        ),
        min_size=1,
        max_size=3,
    ),
    weights=st.tuples(
        st.floats(min_value=0, max_value=1),
        st.floats(min_value=0, max_value=1),
        st.floats(min_value=0, max_value=1),
    ).filter(lambda t: sum(t) > 0),
)
def test_cross_backend_rank_sorted(monkeypatch, backend_results, weights):
    w1, w2, w3 = weights
    total = w1 + w2 + w3
    cfg = ConfigModel(
        search=SearchConfig(
            bm25_weight=w1 / total,
            semantic_similarity_weight=w2 / total,
            source_credibility_weight=w3 / total,
        )
    )

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    monkeypatch.setattr(Search, "calculate_bm25_scores", lambda q, r: [1.0] * len(r))
    monkeypatch.setattr(Search, "calculate_semantic_similarity", lambda q, r, query_embedding=None: [1.0] * len(r))
    monkeypatch.setattr(Search, "assess_source_credibility", lambda r: [1.0] * len(r))

    ranked = Search.cross_backend_rank("q", backend_results)
    scores = [res["relevance_score"] for res in ranked]
    assert scores == sorted(scores, reverse=True)


@given(
    results=st.lists(
        st.fixed_dictionaries({"title": st.text(min_size=1), "url": st.just("https://example.com")}),
        min_size=1,
        max_size=5,
    ),
    weights=st.tuples(
        st.floats(min_value=0, max_value=1),
        st.floats(min_value=0, max_value=1),
        st.floats(min_value=0, max_value=1),
    ).filter(lambda t: abs(sum(t) - 1.0) > 0.001),
)
def test_rank_results_invalid_sum(monkeypatch, results, weights):
    w1, w2, w3 = weights
    cfg = ConfigModel.model_construct(
        search=SearchConfig.model_construct(
            bm25_weight=w1,
            semantic_similarity_weight=w2,
            source_credibility_weight=w3,
        )
    )

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    monkeypatch.setattr(Search, "calculate_bm25_scores", lambda q, r: [1.0] * len(r))
    monkeypatch.setattr(Search, "calculate_semantic_similarity", lambda q, r, query_embedding=None: [1.0] * len(r))
    monkeypatch.setattr(Search, "assess_source_credibility", lambda r: [1.0] * len(r))

    with pytest.raises(ConfigError):
        Search.rank_results("q", results)
