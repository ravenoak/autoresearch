import math

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
