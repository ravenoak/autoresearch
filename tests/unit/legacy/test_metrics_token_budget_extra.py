# mypy: ignore-errors
from autoresearch.orchestration.metrics import OrchestrationMetrics


def test_compress_prompt_threshold():
    m = OrchestrationMetrics()
    long = "x " * 20
    m.compress_prompt_if_needed(long.strip(), 5)
    res = m.compress_prompt_if_needed("short prompt", 5, threshold=0.9)
    assert len(res.split()) <= 5


def test_suggest_token_budget_shrink():
    m = OrchestrationMetrics()
    m.record_tokens("A", 1, 1)
    m.record_tokens("A", 1, 1)
    new = m.suggest_token_budget(10, margin=0.1)
    assert new < 10
