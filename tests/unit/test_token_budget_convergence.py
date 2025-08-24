"""Convergence checks for ``suggest_token_budget``.

The mathematical proof appears in ``docs/algorithms/token_budgeting.md``.
"""

import math
from typing import List

from hypothesis import given
from hypothesis import strategies as st

from autoresearch.orchestration.metrics import OrchestrationMetrics


def _run_cycles(metrics: OrchestrationMetrics, usage: List[int], margin: float, start: int) -> int:
    budget = start
    for u in usage:
        metrics.record_tokens("agent", u, 0)
        budget = metrics.suggest_token_budget(budget, margin=margin)
    return budget


def test_suggest_token_budget_converges() -> None:
    """Repeated updates reach ``ceil(u * (1 + m))`` for constant usage.

    See ``docs/algorithms/token_budgeting.md`` for the formal proof.
    """
    m = OrchestrationMetrics()
    budget = _run_cycles(m, [50] * 8, margin=0.2, start=50)
    assert budget == math.ceil(50 * 1.2 - 1e-9)


def test_budget_tracks_growth() -> None:
    """Sustained increases raise the budget to the new level."""
    m = OrchestrationMetrics()
    usage = [30, 30, 50, 50, 50]
    budget = _run_cycles(m, usage, margin=0.2, start=usage[0])
    assert budget == math.ceil(50 * 1.2 - 1e-9)


def test_budget_recovers_after_spike() -> None:
    """A one-off spike does not inflate the long-term budget."""
    m = OrchestrationMetrics()
    usage = [50, 80] + [50] * 20
    budget = _run_cycles(m, usage, margin=0.2, start=usage[0])
    assert budget == math.ceil(50 * 1.2 - 1e-9)


def test_margin_precision_converges() -> None:
    """Decimal margins avoid rounding inflation."""
    m = OrchestrationMetrics()
    budget = _run_cycles(m, [50] * 8, margin=0.1, start=50)
    assert budget == math.ceil(50 * 1.1 - 1e-9)


@given(
    start=st.integers(min_value=0, max_value=120),
    margin=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
def test_convergence_from_any_start(start: int, margin: float) -> None:
    """Budgets converge to ceil(u * (1 + m)) from arbitrary starts."""
    m = OrchestrationMetrics()
    usage = [50] * 6
    budget = _run_cycles(m, usage, margin=margin, start=start)
    assert budget == math.ceil(50 * (1 + margin) - 1e-9)


@given(
    start=st.integers(min_value=1, max_value=120),
    margin=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
def test_zero_usage_bottoms_out(start: int, margin: float) -> None:
    """Zero usage drives the budget down to one token."""
    m = OrchestrationMetrics()
    # First cycle with usage to enable shrinkage
    m.record_tokens("agent", 10, 0)
    budget = m.suggest_token_budget(start, margin=margin)
    for _ in range(10):
        budget = m.suggest_token_budget(budget, margin=margin)
    assert budget == 1


@given(
    start=st.integers(min_value=0, max_value=500),
    margin=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
def test_initial_call_without_usage_keeps_budget(start: int, margin: float) -> None:
    """No usage history leaves the budget unchanged, even when zero."""
    m = OrchestrationMetrics()
    assert m.suggest_token_budget(start, margin=margin) == start


@given(
    start=st.integers(min_value=0, max_value=500),
    usage=st.integers(min_value=1, max_value=500),
    margin=st.sampled_from([-0.5, 0.0, 0.1, 1.0]),
)
def test_margin_boundaries_converge(start: int, usage: int, margin: float) -> None:
    """Budgets converge for negative, zero, decimal, and unit margins."""
    m = OrchestrationMetrics()
    budget = _run_cycles(m, [usage] * 6, margin=margin, start=start)
    expected_margin = max(margin, 0.0)
    assert budget == math.ceil(usage * (1 + expected_margin) - 1e-9)


def test_agent_average_preserves_budget() -> None:
    """Per-agent averages keep the budget elevated after idle cycles."""
    m = OrchestrationMetrics()
    budget = 100
    for _ in range(5):
        m.record_tokens("b", 100, 0)
        budget = m.suggest_token_budget(budget, margin=0.2)
    for _ in range(5):
        m.record_tokens("a", 10, 0)
        budget = m.suggest_token_budget(budget, margin=0.2)
    assert budget == math.ceil(100 * 1.2)


@given(
    first=st.integers(min_value=1, max_value=200),
    second=st.integers(min_value=1, max_value=200),
    gap=st.integers(min_value=10, max_value=30),
    margin=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
def test_sparse_usage_retains_history(first: int, second: int, gap: int, margin: float) -> None:
    """Old non-zero samples influence the average despite long idle gaps."""
    m = OrchestrationMetrics()
    budget = first
    m.record_tokens("agent", first, 0)
    budget = m.suggest_token_budget(budget, margin=margin)
    for _ in range(gap):
        budget = m.suggest_token_budget(budget, margin=margin)
    m.record_tokens("agent", second, 0)
    budget = m.suggest_token_budget(budget, margin=margin)
    expected = math.ceil(max(second, (first + second) / 2) * (1 + margin) - 1e-9)
    assert budget == expected


@given(
    start=st.integers(min_value=0, max_value=500),
    margin=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
def test_budget_lower_bound(start: int, margin: float) -> None:
    """Uninitialized budgets stay fixed; active ones floor at one."""
    m = OrchestrationMetrics()
    budget = m.suggest_token_budget(start, margin=margin)
    if start == 0:
        assert budget == 0
    else:
        assert budget >= 1
