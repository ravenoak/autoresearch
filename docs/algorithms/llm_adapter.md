# LLM Adapter Algorithm

Adapter selection, token accounting, and fallback formulas guide LLM usage.
Adapters are ordered by preference. The first adapter whose estimated token
usage fits the budget is chosen. Estimated tokens follow:

```
expected = prompt_tokens + response_tokens
```

If `expected` exceeds `token_budget`, the next adapter in the list is tried.

Token accounting tracks tokens for each call:

```
in_tokens = len(prompt.split())
out_tokens = len(output.split())
total = in_tokens + out_tokens
```

When `in_tokens` exceeds `token_budget`, prompt compression applies:

```
half = max(1, (token_budget - 1) // 2)
compressed = tokens[:half] + ["..."] + tokens[-half:]
```

If a summarizer is available and produces `summary_tokens <= token_budget`,
that summary replaces the compressed prompt.

These heuristics balance fidelity and cost. Run the simulation script to
explore different budgets and adapter orders.

- [LLM specification](../specs/llm.md)
- [Simulation script](../../scripts/simulate_llm_adapter.py)
