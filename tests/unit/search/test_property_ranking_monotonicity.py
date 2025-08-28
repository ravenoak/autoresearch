from typing import List

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel, SearchConfig
from autoresearch.search import Search


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    bm25_a=st.floats(min_value=0, max_value=1),
    bm25_b=st.floats(min_value=0, max_value=1),
    sem_a=st.floats(min_value=0, max_value=1),
    sem_b=st.floats(min_value=0, max_value=1),
    cred_a=st.floats(min_value=0, max_value=1),
    cred_b=st.floats(min_value=0, max_value=1),
    weights=st.lists(
        st.floats(min_value=0.01, max_value=1.0), min_size=3, max_size=3
    ).map(lambda w: [x / sum(w) for x in w]),
)
def test_monotonic_ranking(
    bm25_a: float,
    bm25_b: float,
    sem_a: float,
    sem_b: float,
    cred_a: float,
    cred_b: float,
    weights: List[float],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If one result dominates across metrics it ranks no lower."""
    docs = [
        {"title": "a", "url": "https://a", "similarity": sem_a},
        {"title": "b", "url": "https://b", "similarity": sem_b},
    ]
    cfg = ConfigModel(
        search=SearchConfig(
            bm25_weight=weights[0],
            semantic_similarity_weight=weights[1],
            source_credibility_weight=weights[2],
            use_bm25=True,
            use_semantic_similarity=True,
            use_source_credibility=True,
        )
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None
    monkeypatch.setattr(
        Search,
        "calculate_bm25_scores",
        staticmethod(lambda q, r: [bm25_a, bm25_b]),
    )
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda self, q, r, query_embedding=None: [sem_a, sem_b],
    )
    monkeypatch.setattr(
        Search,
        "assess_source_credibility",
        lambda self, r: [cred_a, cred_b],
    )

    ranked = Search.rank_results("q", docs)
    score_a, score_b = [r["relevance_score"] for r in ranked]
    if bm25_a >= bm25_b and sem_a >= sem_b and cred_a >= cred_b:
        assert ranked[0]["title"] == "a"
        assert score_a >= score_b
