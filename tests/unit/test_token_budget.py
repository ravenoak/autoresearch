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
    assert cfg.token_budget >= q_tokens
    assert cfg.token_budget <= max(initial_budget, q_tokens * 20)


@given(st.text(min_size=1))
def test_budget_none_unmodified(query):
    cfg = ConfigModel(token_budget=None)
    Orchestrator._apply_adaptive_token_budget(cfg, query)
    assert cfg.token_budget is None
