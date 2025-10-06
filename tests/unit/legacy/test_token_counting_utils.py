from autoresearch.llm.token_counting import compress_prompt, prune_context


def test_compress_prompt_reduces_tokens():
    long_prompt = " ".join(str(i) for i in range(20))
    compressed = compress_prompt(long_prompt, 6)
    assert len(compressed.split()) <= 7
    assert compressed.split()[0] == "0"
    assert compressed.split()[-1] == "19"


def test_prune_context_drops_old_messages():
    msgs = [f"msg{i}" for i in range(10)]
    pruned = prune_context(msgs, 4)
    assert sum(len(m.split()) for m in pruned) <= 4
    assert pruned == msgs[-4:]


def test_compress_prompt_zero_budget_handles_ellipsis():
    prompt = "one two three four"
    compressed = compress_prompt(prompt, 0)
    tokens = compressed.split()
    assert tokens[0] == "one"
    assert tokens[-1] == "four"
    assert "..." in tokens


def test_prune_context_zero_budget_returns_empty():
    msgs = ["a", "b"]
    assert prune_context(msgs, 0) == []
