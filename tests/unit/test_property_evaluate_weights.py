import pytest
import math
from hypothesis import given, strategies as st, settings, HealthCheck

from autoresearch.search import Search
from typing import Any

# generate evaluation data: dictionary mapping query to list of docs


def random_doc():
    return {
        "bm25": st.floats(0, 5),
        "semantic": st.floats(0, 5),
        "credibility": st.floats(0, 1),
        "relevance": st.floats(0, 3),
    }


# property: evaluate_weights scale invariance and bounded output
@settings(suppress_health_check=[HealthCheck.too_slow])
@given(
    data=st.dictionaries(
        st.text(min_size=1, max_size=5),
        st.lists(st.fixed_dictionaries(random_doc()), min_size=1, max_size=5),
        min_size=1,
        max_size=5,
    ),
    weights=st.tuples(
        st.floats(0.1, 1), st.floats(0.1, 1), st.floats(0.1, 1)
    ),
    k=st.floats(0.1, 10),
)
def test_evaluate_weights_scale_invariant(data: Any, weights: Any, k: Any) -> None:
    score1 = Search.evaluate_weights(weights, data)
    scaled = tuple(w * k for w in weights)
    score2 = Search.evaluate_weights(scaled, data)
    assert math.isclose(score1, score2, rel_tol=1e-9)
    assert 0.0 <= score1 <= 1.0


def test_evaluate_weights_empty() -> None:
    with pytest.raises(ZeroDivisionError):
        Search.evaluate_weights((0.5, 0.3, 0.2), {})
