import math

from hypothesis import given
from hypothesis import strategies as st

from autoresearch.orchestration.metrics import OrchestrationMetrics


def test_suggest_token_budget_converges() -> None:
    """Repeated updates reach ceil(u * (1 + m)) for constant usage."""
    m = OrchestrationMetrics()
    usage = 50
    budget = usage
    for _ in range(8):
        m.token_usage_history.append(usage)
        budget = m.suggest_token_budget(budget, margin=0.2)
    assert budget == math.ceil(usage * 1.2)


def test_budget_tracks_growth() -> None:
    """Sustained increases raise the budget to the new level."""
    m = OrchestrationMetrics()
    usage_pattern = [30, 30, 50, 50, 50]
    budget = usage_pattern[0]
    for u in usage_pattern:
        m.token_usage_history.append(u)
        budget = m.suggest_token_budget(budget, margin=0.2)
    assert budget == math.ceil(50 * 1.2)


def test_budget_recovers_after_spike() -> None:
    """A one-off spike does not inflate the long-term budget."""
    m = OrchestrationMetrics()
    usage_pattern = [50, 80] + [50] * 20
    budget = usage_pattern[0]
    for u in usage_pattern:
        m.token_usage_history.append(u)
        budget = m.suggest_token_budget(budget, margin=0.2)
    assert budget == math.ceil(50 * 1.2)


@given(
    start=st.integers(min_value=1, max_value=120),
    margin=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
def test_convergence_from_any_start(start: int, margin: float) -> None:
    """Budgets converge to ceil(u * (1 + m)) from arbitrary starts."""
    m = OrchestrationMetrics()
    usage = 50
    budget = start
    for _ in range(6):
        m.token_usage_history.append(usage)
        budget = m.suggest_token_budget(budget, margin=margin)
    assert budget == math.ceil(usage * (1 + margin))


@given(
    start=st.integers(min_value=1, max_value=120),
    margin=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
def test_zero_usage_bottoms_out(start: int, margin: float) -> None:
    """Zero usage drives the budget down to one token."""
    m = OrchestrationMetrics()
    budget = start
    for _ in range(5):
        m.token_usage_history.append(0)
        budget = m.suggest_token_budget(budget, margin=margin)
    assert budget == 1


@given(
    start=st.integers(min_value=1, max_value=500),
    margin=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
def test_initial_call_without_usage_keeps_budget(start: int, margin: float) -> None:
    """No usage history leaves the budget unchanged."""
    m = OrchestrationMetrics()
    assert m.suggest_token_budget(start, margin=margin) == start


@given(
    start=st.integers(min_value=1, max_value=500),
    usage=st.integers(min_value=1, max_value=500),
    margin=st.sampled_from([0.0, 1.0]),
)
def test_margin_extremes_converge(start: int, usage: int, margin: float) -> None:
    """Budgets converge for margin 0 and 1."""
    m = OrchestrationMetrics()
    budget = start
    for _ in range(6):
        m.token_usage_history.append(usage)
        budget = m.suggest_token_budget(budget, margin=margin)
    assert budget == math.ceil(usage * (1 + margin))
