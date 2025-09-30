from __future__ import annotations

import string

from hypothesis import HealthCheck, given, settings, strategies as st

from autoresearch.search import Search
from autoresearch.config.models import ConfigModel, SearchConfig
from autoresearch.config.loader import ConfigLoader
import pytest
from typing import Any


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
    monkeypatch.setattr(
        Search, "calculate_bm25_scores", staticmethod(lambda q, r: [1.0] * len(r))
    )
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda self, q, r, query_embedding=None: [1.0] * len(r),
    )
    monkeypatch.setattr(Search, "assess_source_credibility", lambda self, r: [1.0] * len(r))


@given(
    st.lists(
        st.text(alphabet=string.ascii_lowercase, min_size=1),
        min_size=1,
        max_size=5,
        unique=True,
    )
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_rank_results_preserves_input_order(monkeypatch: pytest.MonkeyPatch, titles: Any) -> None:
    """Ranking should be stable when scores are identical."""
    results = [
        {"title": t, "url": f"https://example.com/{i}"} for i, t in enumerate(titles)
    ]
    _setup(monkeypatch)
    ranked = Search.rank_results("q", results)
    assert [r["title"] for r in ranked] == [r["title"] for r in results]
