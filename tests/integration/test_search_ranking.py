from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from autoresearch.search import rank_by_recency_and_relevance


@pytest.mark.integration
def test_rank_results_respects_weights() -> None:
    now = datetime.now(UTC)
    results = [
        {"id": "old_high", "relevance": 0.9, "timestamp": (now - timedelta(days=10)).isoformat()},
        {"id": "new_low", "relevance": 0.1, "timestamp": now.isoformat()},
    ]
    ranked = rank_by_recency_and_relevance(results, recency_weight=0.8)
    assert [r["id"] for r in ranked] == ["new_low", "old_high"]


@pytest.mark.integration
def test_rank_results_stable_order() -> None:
    now = datetime.now(UTC)
    results = [
        {"id": "a", "relevance": 0.5, "timestamp": now.isoformat()},
        {"id": "b", "relevance": 0.5, "timestamp": now.isoformat()},
    ]
    ranked = rank_by_recency_and_relevance(results, recency_weight=0.5)
    assert [r["id"] for r in ranked] == ["a", "b"]
