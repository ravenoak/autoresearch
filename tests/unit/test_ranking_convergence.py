from typing import NotRequired, Sequence, TypedDict

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


class RankingResult(TypedDict):
    """Mutable ranking record containing component scores."""

    id: int
    bm25: float
    semantic: float
    cred: float
    score: NotRequired[float]


def rank_once(results: list[RankingResult]) -> list[RankingResult]:
    """Rank results by a fixed weighted score."""
    weights: dict[str, float] = {"bm25": 0.5, "semantic": 0.3, "cred": 0.2}
    for record in results:
        record["score"] = sum(record[key] * weight for key, weight in weights.items())
    return sorted(results, key=lambda record: record["score"], reverse=True)


def inversion_distance(order: Sequence[int], target: Sequence[int]) -> int:
    pos: dict[int, int] = {oid: idx for idx, oid in enumerate(target)}
    count = 0
    for i, anchor in enumerate(order):
        for follower in order[i + 1 :]:
            if pos[anchor] > pos[follower]:
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
def test_ranking_monotonic(scores: list[tuple[float, float, float]]) -> None:
    """Inversion count decreases with each ranking iteration."""
    results: list[RankingResult] = [
        {"id": i, "bm25": b, "semantic": s, "cred": c}
        for i, (b, s, c) in enumerate(scores)
    ]
    initial: list[int] = [record["id"] for record in results]
    ranked1: list[RankingResult] = rank_once(results)
    order1: list[int] = [record["id"] for record in ranked1]
    ranked2: list[RankingResult] = rank_once(ranked1)
    order2: list[int] = [record["id"] for record in ranked2]
    target: list[int] = order2
    i0: int = inversion_distance(initial, target)
    i1: int = inversion_distance(order1, target)
    i2: int = inversion_distance(order2, target)
    assert i1 <= i0
    assert i2 <= i1
