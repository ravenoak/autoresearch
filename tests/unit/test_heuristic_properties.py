import pytest
from hypothesis import assume, given, strategies as st

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
    baseline=st.integers(min_value=1, max_value=50),
    delta=st.integers(min_value=0, max_value=50),
)
def test_token_budget_monotonicity(baseline, delta):
    small = baseline
    large = baseline + delta
    metrics_small = OrchestrationMetrics()
    metrics_large = OrchestrationMetrics()
    metrics_small.record_tokens("a", small, 0)
    metrics_large.record_tokens("a", large, 0)
    budget_small = metrics_small.suggest_token_budget(10)
    budget_large = metrics_large.suggest_token_budget(10)
    assert budget_large >= budget_small


@pytest.mark.unit
def test_token_budget_monotonicity_deterministic():
    metrics_small = OrchestrationMetrics()
    metrics_large = OrchestrationMetrics()

    baseline_budget = 10
    baseline_usage = 5

    metrics_small.record_tokens("agent", baseline_usage, 0)
    metrics_large.record_tokens("agent", baseline_usage, 0)

    current_small = metrics_small.suggest_token_budget(baseline_budget)
    current_large = metrics_large.suggest_token_budget(baseline_budget)
    assert current_small == current_large

    metrics_small.record_tokens("agent", baseline_usage, 0)
    metrics_large.record_tokens("agent", baseline_usage + 3, 0)

    next_small = metrics_small.suggest_token_budget(current_small)
    next_large = metrics_large.suggest_token_budget(current_large)

    assert next_large >= next_small
    assert next_small >= 1


@pytest.mark.unit
def test_token_budget_zero_usage_regression():
    idle = OrchestrationMetrics()
    active = OrchestrationMetrics()
    idle.record_tokens("a", 0, 0)
    active.record_tokens("a", 1, 0)
    assert idle.suggest_token_budget(10) == 10
    assert active.suggest_token_budget(10) == 1
