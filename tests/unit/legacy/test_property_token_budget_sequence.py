# mypy: ignore-errors
import pytest
from hypothesis import given, strategies as st

from autoresearch.orchestration.metrics import OrchestrationMetrics


@pytest.mark.unit
@given(st.lists(st.integers(min_value=0, max_value=5), min_size=1, max_size=5))
def test_token_budget_sequence_monotonic(usages):
    metrics = OrchestrationMetrics()
    last = 0
    total = 0
    for inc in usages:
        total += inc
        budget = metrics.suggest_token_budget(total)
        assert budget >= last
        last = budget
