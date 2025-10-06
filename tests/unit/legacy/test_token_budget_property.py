from __future__ import annotations

from hypothesis import given, strategies as st

from autoresearch.llm.token_counting import compress_prompt, prune_context


@given(st.text(min_size=1), st.integers(min_value=3, max_value=50))
def test_compress_prompt_respects_budget(prompt: str, budget: int) -> None:
    result = compress_prompt(prompt, budget)
    assert len(result.split()) <= budget


@given(st.lists(st.text(min_size=1), max_size=10), st.integers(min_value=0, max_value=50))
def test_prune_context_keeps_latest_items(context: list[str], budget: int) -> None:
    pruned = prune_context(context, budget)
    assert sum(len(c.split()) for c in pruned) <= budget
    assert pruned == context[len(context) - len(pruned) :]
