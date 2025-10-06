from autoresearch.orchestration.metrics import OrchestrationMetrics


def test_compress_prompt_if_needed():
    m = OrchestrationMetrics()
    prompt = "one two three four five"
    compressed = m.compress_prompt_if_needed(prompt, 3)
    assert len(compressed.split()) <= 3
    assert m.compress_prompt_if_needed(prompt, 6) == prompt


def test_suggest_token_budget():
    m = OrchestrationMetrics()
    m.record_tokens("A", 5, 5)
    assert m.suggest_token_budget(8) == 11
    assert m.suggest_token_budget(20) == 11
