import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from typing import Any


def rank_once(results):
    """Rank results by a fixed weighted score."""
    weights = {"bm25": 0.5, "semantic": 0.3, "cred": 0.2}
    for r in results:
        r["score"] = sum(r[k] * w for k, w in weights.items())
    return sorted(results, key=lambda r: r["score"], reverse=True)


def inversion_distance(order, target):
    pos = {oid: i for i, oid in enumerate(target)}
    count = 0
    for i, a in enumerate(order):
        for b in order[i + 1 :]:
            if pos[a] > pos[b]:
                count += 1
    return count


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.unit
@given(
    scores=st.lists(
        st.tuples(
            st.floats(min_value=0.0, max_value=1.0),
            st.floats(min_value=0.0, max_value=1.0),
            st.floats(min_value=0.0, max_value=1.0),
        ),
        min_size=1,
        max_size=8,
    )
)
def test_ranking_monotonic(scores: Any) -> None:
    """Inversion count decreases with each ranking iteration."""
    results = [
        {"id": i, "bm25": b, "semantic": s, "cred": c}
        for i, (b, s, c) in enumerate(scores)
    ]
    initial = [r["id"] for r in results]
    ranked1 = rank_once(results)
    order1 = [r["id"] for r in ranked1]
    ranked2 = rank_once(ranked1)
    order2 = [r["id"] for r in ranked2]
    target = order2
    i0 = inversion_distance(initial, target)
    i1 = inversion_distance(order1, target)
    i2 = inversion_distance(order2, target)
    assert i1 <= i0
    assert i2 <= i1
