import math
from decimal import Decimal, ROUND_CEILING

from hypothesis import given
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
    assert budget == 29


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
    target = math.ceil(usage * (1 + margin))
    assert budget == target
    for _ in range(3):
        m.record_tokens("agent", usage, 0)
        budget = m.suggest_token_budget(budget, margin=margin)
        assert budget == target


@given(
    usage=st.integers(min_value=1, max_value=100),
    margin=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
def test_budget_rounds_up(usage: int, margin: float) -> None:
    """The update uses ceiling rounding on the scaled usage."""
    m = OrchestrationMetrics()
    budget = usage
    for _ in range(6):
        m.record_tokens("agent", usage, 0)
        budget = m.suggest_token_budget(budget, margin=margin)
    scaled = Decimal(str(usage)) * (Decimal("1") + Decimal(str(margin)))
    expected = int(scaled.to_integral_value(rounding=ROUND_CEILING))
    assert budget == expected
