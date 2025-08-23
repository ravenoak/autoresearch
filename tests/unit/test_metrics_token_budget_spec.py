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
    assert budget == 56
    m.record_tokens("A", 1, 0)
    budget = m.suggest_token_budget(budget, margin=0.1)
    assert budget == 29


def test_token_budget_never_below_one():
    m = OrchestrationMetrics()
    budget = 2
    m.record_tokens("A", 0, 0)
    budget = m.suggest_token_budget(budget, margin=0.5)
    assert budget == 1
