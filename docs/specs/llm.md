# Llm

## Overview

Language Model (LLM) integration module for Autoresearch. See
[adapter selection and token accounting][a1] for switching heuristics and
fallback formulas.

## Algorithms

### Adapter selection

1. Build an ordered list of candidate adapters.
2. For each name:
   - Look up the class in the `registry`.
   - Instantiate and call ``validate_model``.
   - On failure, record the error and try the next adapter.
3. Return the first adapter that succeeds.
4. If none succeed, fall back to `DummyAdapter`.

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
per-agent spikes. The budget is enforced by `compress_prompt`, which
truncates the middle of an over-long prompt or delegates to a summarizer. See
also [token budgeting algorithm][a2].

### Formal reasoning

#### Adapter selection

Let ``A`` be the ordered list of adapter names. The procedure performs a
linear scan over ``A`` and invokes ``validate_model`` on each candidate. If a
candidate succeeds the search stops, yielding the first compatible adapter.
Should every candidate fail, the algorithm falls back to ``DummyAdapter``. The
strategy is therefore complete, deterministic, and runs in ``O(|A|)`` time.

#### Token budgeting

Define ``C = {latest, avg_used, max_agent_delta, max_agent_avg}`` and margin
``m >= 0``. The update computes ``b = max(round(max(C) * (1 + m)), 1)``. Each
element of ``C`` upper-bounds recent usage, so ``b`` always covers the largest
observed load. Flooring at one prevents the orchestrator from stalling when
usage temporarily drops to zero.

### Mathematical analysis

#### Budget convergence

Let usage stabilize at ``u`` tokens per cycle. With margin ``m`` the fixed
point is ``b* = ceil(u * (1 + m))``. Any pre-spike value ``U`` persists in the
averages for at most ten cycles. As history fills with ``u`` the maximum
candidate decreases monotonically to ``u`` and the update yields ``b*``. Thus
convergence occurs within ten steady cycles. See [token budgeting
algorithm][a2] for the derivation.

#### Worst-case prompt compression

Assume a prompt with ``n`` tokens and budget ``b >= 3``. Without a summarizer,
``compress_prompt`` keeps ``h = floor((b - 1) / 2)`` tokens from each end and
inserts an ellipsis, producing at most ``2h + 1 <= b`` tokens. When a
summarizer is provided its output must already respect ``b``; otherwise the
fallback truncation applies. Budgets below three require a summarizer to remain
within bounds.

## Invariants

- Preserve documented state across operations.

## Proof Sketch

Core routines enforce invariants by validating inputs and state.

## Simulation Expectations

- ``test_llm_adapter`` exercises summarizer and ellipsis fallback.
- ``test_token_usage`` verifies adaptive budgeting and prompt truncation.
- ``test_llm_capabilities`` uses default capability maps when probing fails.

[a1]: ../algorithms/llm_adapter.md
[a2]: ../algorithms/token_budgeting.md
