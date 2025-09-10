# Llm

## Overview

Language Model (LLM) integration module for Autoresearch. See
[adapter selection and token accounting][a1] for switching heuristics and
fallback formulas.

## Algorithms

### Adapter selection

1. Build an ordered list of candidate adapters.
2. For each name:
   - Look up the class in the [registry][m4].
   - Instantiate and call ``validate_model``.
   - On failure, record the error and try the next adapter.
3. Return the first adapter that succeeds.
4. If none succeed, fall back to [DummyAdapter][m2].

### Token budgeting

Given cycle usage values:

```
margin = max(m, 0)
candidates = [latest, avg_used, max_agent_delta, max_agent_avg]
desired = round(max(candidates) * (1 + margin))
budget = max(desired, 1)
```

``latest`` is usage in the most recent cycle, ``avg_used`` is the mean across
recent non-zero cycles, and ``max_agent_delta`` and ``max_agent_avg`` capture
per-agent spikes. The budget is enforced by [`compress_prompt`][m3], which
truncates the middle of an over-long prompt or delegates to a summarizer. See
also [token budgeting algorithm][a2].

## Invariants

- Preserve documented state across operations.

## Proof Sketch

Core routines enforce invariants by validating inputs and state.

## Simulation Expectations

- ``test_llm_adapter`` exercises summarizer and ellipsis fallback.
- ``test_token_usage`` verifies adaptive budgeting and prompt truncation.
- ``test_llm_capabilities`` uses default capability maps when probing fails.

## Traceability

- Modules
  - [adapters.py][m2]
  - [token_counting.py][m3]
  - [capabilities.py][m5]
  - [registry.py][m4]
- Tests
  - [test_agents_llm.py][t1]
  - [test_llm_adapter.py][t2]
  - [test_token_usage.py][t4]
  - [test_llm_capabilities.py][t3]

[a1]: ../algorithms/llm_adapter.md
[a2]: ../algorithms/token_budgeting.md
[m2]: ../../src/autoresearch/llm/adapters.py
[m3]: ../../src/autoresearch/llm/token_counting.py
[m4]: ../../src/autoresearch/llm/registry.py
[m5]: ../../src/autoresearch/llm/capabilities.py
[t1]: ../../tests/unit/test_agents_llm.py
[t2]: ../../tests/unit/test_llm_adapter.py
[t3]: ../../tests/unit/test_llm_capabilities.py
[t4]: ../../tests/unit/test_token_usage.py
