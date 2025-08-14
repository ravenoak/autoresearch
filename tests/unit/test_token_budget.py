from hypothesis import given, strategies as st

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.orchestration_utils import OrchestrationUtils
from autoresearch.orchestration.metrics import OrchestrationMetrics


@given(st.integers(min_value=1, max_value=4000), st.text(min_size=1, max_size=200))
def test_budget_within_bounds(initial_budget, query):
    cfg = ConfigModel(token_budget=initial_budget)
    OrchestrationUtils.apply_adaptive_token_budget(cfg, query)
    q_tokens = len(query.split())
    max_budget = max(initial_budget // cfg.loops, q_tokens * 20)
    assert cfg.token_budget >= q_tokens
    assert cfg.token_budget <= max_budget


@given(st.text(min_size=1))
def test_budget_none_unmodified(query):
    cfg = ConfigModel(token_budget=None)
    OrchestrationUtils.apply_adaptive_token_budget(cfg, query)
    assert cfg.token_budget is None


@given(
    st.integers(min_value=1, max_value=4000),
    st.integers(min_value=1, max_value=10),
    st.integers(min_value=1, max_value=20),
)
def test_budget_scaling_exact(initial_budget, loops, q_tokens):
    query = " ".join("x" for _ in range(q_tokens))
    cfg = ConfigModel(token_budget=initial_budget, loops=loops)
    OrchestrationUtils.apply_adaptive_token_budget(cfg, query)

    budget = initial_budget
    if loops > 1:
        budget = max(1, budget // loops)
    max_budget = q_tokens * 20
    if budget > max_budget:
        expected = max_budget
    elif budget < q_tokens:
        expected = q_tokens + 10
    else:
        expected = budget

    assert cfg.token_budget == expected


def test_budget_adaptive_history():
    m = OrchestrationMetrics()
    budget = 10

    m.record_tokens("A", 3, 2)
    budget = m.suggest_token_budget(budget)
    assert budget == 5

    m.record_tokens("A", 10, 5)
    budget = m.suggest_token_budget(budget)
    assert budget == 16

    m.record_tokens("A", 9, 0)
    budget = m.suggest_token_budget(budget)
    assert budget == 10


def test_compress_prompt_history():
    m = OrchestrationMetrics()
    budget = 5
    prompt = "one two three four five"
    assert m.compress_prompt_if_needed(prompt, budget) == prompt

    long_prompt = "one two three four five six seven eight"
    compressed = m.compress_prompt_if_needed(long_prompt, budget)
    assert len(compressed.split()) <= budget

    compressed_again = m.compress_prompt_if_needed(prompt, budget)
    assert len(compressed_again.split()) <= budget
