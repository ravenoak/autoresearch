import pytest
from decimal import Decimal, ROUND_HALF_EVEN

from hypothesis import assume, given
from hypothesis import strategies as st

from autoresearch.orchestration.metrics import OrchestrationMetrics


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


@pytest.mark.xfail(reason="budget floor not enforced", strict=False)
def test_token_budget_never_below_one():
    m = OrchestrationMetrics()
    budget = 2
    m.record_tokens("A", 0, 0)
    budget = m.suggest_token_budget(budget, margin=0.5)
    assert budget == 1


@given(
    usage=st.integers(min_value=1, max_value=100),
    n=st.integers(min_value=0, max_value=200),
)
def test_rounding_half_cases(usage: int, n: int) -> None:
    """Calculated budgets follow Decimal half-even rounding."""
    margin = (2 * n + 1) / (2 * usage) - 1
    assume(0.0 <= margin <= 1.0)
    m = OrchestrationMetrics()
    budget = usage
    for _ in range(6):
        m.record_tokens("agent", usage, 0)
        budget = m.suggest_token_budget(budget, margin=margin)
    scaled = Decimal(str(usage)) * (Decimal("1") + Decimal(str(margin)))
    expected = int(scaled.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))
    assert budget == expected
