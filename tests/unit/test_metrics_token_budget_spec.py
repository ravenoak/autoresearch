from hypothesis import given
from hypothesis import strategies as st

from autoresearch.orchestration.metrics import OrchestrationMetrics
from autoresearch.token_budget import round_with_margin


def test_compression_threshold_reduces_with_history(monkeypatch):
    m = OrchestrationMetrics()
    long_prompt = "x " * 20
    m.compress_prompt_if_needed(long_prompt.strip(), 5)

    called = {}

    def fake_compress(prompt: str, budget: int) -> str:
        called["used"] = True
        return "short"

    monkeypatch.setattr("autoresearch.llm.token_counting.compress_prompt", fake_compress)

    result = m.compress_prompt_if_needed("one two three four five", 5)
    assert called["used"] is True
    assert result == "short"


def test_token_budget_expands_then_shrinks():
    m = OrchestrationMetrics()
    budget = 10
    m.record_tokens("A", 50, 0)
    budget = m.suggest_token_budget(budget, margin=0.1)
    assert budget == 55
    m.record_tokens("A", 1, 0)
    budget = m.suggest_token_budget(budget, margin=0.1)
    assert budget == 28


def test_budget_shrinks_to_one_after_zero_usage():
    m = OrchestrationMetrics()
    budget = 20
    m.record_tokens("A", 5, 0)
    budget = m.suggest_token_budget(budget, margin=0.2)
    for _ in range(10):
        m.record_tokens("A", 0, 0)
        budget = m.suggest_token_budget(budget, margin=0.2)
    assert budget == 1


def test_budget_converges_for_constant_usage():
    m = OrchestrationMetrics()
    margin = 0.2
    usage = 50
    budget = 1
    for _ in range(12):
        m.record_tokens("agent", usage, 0)
        budget = m.suggest_token_budget(budget, margin=margin)
    target = round_with_margin(usage, margin)
    assert budget == target
    for _ in range(3):
        m.record_tokens("agent", usage, 0)
        budget = m.suggest_token_budget(budget, margin=margin)
        assert budget == target


@given(
    usage=st.integers(min_value=1, max_value=100),
    margin=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
def test_budget_rounds_half_up(usage: int, margin: float) -> None:
    """The update uses round-half-up on the scaled usage."""
    m = OrchestrationMetrics()
    budget = usage
    for _ in range(6):
        m.record_tokens("agent", usage, 0)
        budget = m.suggest_token_budget(budget, margin=margin)
    expected = round_with_margin(usage, margin)
    assert budget == expected


def test_budget_respects_bounds_during_spike():
    m = OrchestrationMetrics()
    margin = 0.2
    spike = 100
    usage = 10
    budget = 5
    m.record_tokens("agent", spike, 0)
    budget = m.suggest_token_budget(budget, margin=margin)
    target = round_with_margin(usage, margin)
    upper = round_with_margin(spike, margin)
    for _ in range(10):
        m.record_tokens("agent", usage, 0)
        budget = m.suggest_token_budget(budget, margin=margin)
        assert target <= budget <= upper
    assert budget == target


@given(
    spike=st.integers(min_value=1, max_value=200),
    usage=st.integers(min_value=1, max_value=200),
    margin=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    start=st.integers(min_value=1, max_value=200),
)
def test_convergence_bound_holds(spike: int, usage: int, margin: float, start: int) -> None:
    """Bounds align with docs/algorithms/token_budgeting.md and SPEC_COVERAGE."""
    m = OrchestrationMetrics()
    budget = start
    m.record_tokens("agent", spike, 0)
    budget = m.suggest_token_budget(budget, margin=margin)
    target = round_with_margin(usage, margin)
    upper = round_with_margin(max(spike, usage), margin)
    for _ in range(10):
        m.record_tokens("agent", usage, 0)
        budget = m.suggest_token_budget(budget, margin=margin)
        assert target <= budget <= upper
    assert budget == target
