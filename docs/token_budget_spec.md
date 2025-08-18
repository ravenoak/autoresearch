# Token Budget Helpers Specification

This specification outlines expected behaviors for the token budgeting helpers in `autoresearch.orchestration.metrics`.

## `compress_prompt_if_needed`
- Records each prompt length to track a running average.
- Computes an adjusted threshold:
  - Starts with the provided `threshold` (default `1.0`).
  - If the average length exceeds the `token_budget`, the threshold becomes `min(threshold, token_budget / avg_length)`.
- Returns the original prompt when `tokens <= token_budget * adjusted_threshold`.
- Otherwise invokes `llm.token_counting.compress_prompt` to produce text whose token count does not exceed `token_budget`.
- The historical average allows later prompts to be compressed earlier when recent prompts were long.

## `suggest_token_budget`
- Tracks total tokens and per-agent usage between calls.
- Computes `delta` as tokens used since the last invocation and maintains historical averages.
- Defines thresholds from the current budget:
  - `expand_threshold = current_budget * (1 + margin)`
  - `shrink_threshold = current_budget * (1 - margin)`
- Expands the budget to `max(int(max(delta, avg_used) * (1 + margin)), 1)` when `delta > expand_threshold` **or** `avg_used > current_budget`.
- Shrinks the budget to `max(int(avg_used * (1 + margin)), 1)` when `delta < shrink_threshold` **and** `avg_used < shrink_threshold`.
- Otherwise returns `max(current_budget, 1)`.
- Budgets are never allowed to drop below `1` token.

## Tests
Unit tests in `tests/unit/test_metrics_token_budget_spec.py` exercise:
- Threshold adaptation based on prompt history.
- Budget expansion after a spike and shrinkage when usage falls.
- Enforcement of the minimum budget of one token.
