from hypothesis import given, strategies as st

from autoresearch.config import ConfigModel
from autoresearch.orchestration.orchestrator import Orchestrator


@given(
    st.integers(min_value=1, max_value=4000),
    st.text(min_size=1, max_size=200)
)
def test_budget_within_bounds(initial_budget, query):
    cfg = ConfigModel(token_budget=initial_budget)
    Orchestrator._apply_adaptive_token_budget(cfg, query)
    q_tokens = len(query.split())
    max_budget = max(initial_budget // cfg.loops, q_tokens * 20)
    assert cfg.token_budget >= q_tokens
    assert cfg.token_budget <= max_budget


@given(st.text(min_size=1))
def test_budget_none_unmodified(query):
    cfg = ConfigModel(token_budget=None)
    Orchestrator._apply_adaptive_token_budget(cfg, query)
    assert cfg.token_budget is None


@given(
    st.integers(min_value=1, max_value=4000),
    st.integers(min_value=1, max_value=10),
    st.integers(min_value=1, max_value=20),
)
def test_budget_scaling_exact(initial_budget, loops, q_tokens):
    query = " ".join("x" for _ in range(q_tokens))
    cfg = ConfigModel(token_budget=initial_budget, loops=loops)
    Orchestrator._apply_adaptive_token_budget(cfg, query)

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
