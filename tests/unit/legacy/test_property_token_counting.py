# mypy: ignore-errors
from hypothesis import given, strategies as st, settings, HealthCheck
import string

from autoresearch.llm.token_counting import compress_prompt, prune_context


@settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
@given(
    words=st.lists(st.text(alphabet=string.ascii_letters, min_size=1, max_size=5), min_size=3, max_size=20),
    budget=st.integers(min_value=1, max_value=20),
)
def test_compress_prompt_preserves_edges(words, budget):
    prompt = " ".join(words)
    compressed = compress_prompt(prompt, budget)
    c_tokens = compressed.split()
    assert c_tokens[0] == words[0]
    assert c_tokens[-1] == words[-1]
    assert len(c_tokens) <= max(budget, 3)


@settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
@given(
    messages=st.lists(st.text(alphabet=string.ascii_letters, min_size=1, max_size=5), min_size=0, max_size=10),
    budget=st.integers(min_value=0, max_value=20),
)
def test_prune_context_respects_budget(messages, budget):
    pruned = prune_context(messages, budget)
    total = sum(len(m.split()) for m in pruned)
    assert total <= budget
    if sum(len(m.split()) for m in messages) <= budget:
        assert pruned == messages
