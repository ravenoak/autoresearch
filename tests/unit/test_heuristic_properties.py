import pytest
from hypothesis import given, strategies as st, assume

from autoresearch.orchestration.metrics import OrchestrationMetrics


@pytest.mark.unit
@given(
    scores=st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=3, max_size=3),
    weights=st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=3, max_size=3),
)
def test_weighted_score_normalization(scores, weights):
    total = sum(weights)
    assume(total > 0)
    weights = [w / total for w in weights]
    final = sum(s * w for s, w in zip(scores, weights))
    assert 0.0 <= final <= 1.0


@pytest.mark.unit
@given(
    small=st.integers(min_value=0, max_value=50),
    large=st.integers(min_value=0, max_value=50),
)
def test_token_budget_monotonicity(small, large):
    assume(large >= small)
    m1, m2 = OrchestrationMetrics(), OrchestrationMetrics()
    m1.record_tokens("a", small, 0)
    m2.record_tokens("a", large, 0)
    b1 = m1.suggest_token_budget(10)
    b2 = m2.suggest_token_budget(10)
    assert b2 >= b1
