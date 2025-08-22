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
