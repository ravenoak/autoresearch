# Token Budget Helpers Specification

This specification outlines expected behaviors for the token budgeting
helpers in `autoresearch.orchestration.metrics`.

## `compress_prompt_if_needed`
- Records each prompt length to track a running average.
- Computes an adjusted threshold:
  - Starts with the provided `threshold` (default `1.0`).
  - If the average length exceeds the `token_budget`, the threshold becomes
    `min(threshold, token_budget / avg_length)`.
- Returns the original prompt when
  `tokens <= token_budget * adjusted_threshold`.
- Otherwise invokes `llm.token_counting.compress_prompt` to produce text
  whose token count does not exceed `token_budget`.
- The historical average allows later prompts to be compressed earlier when
  recent prompts were long.

## `suggest_token_budget`
- Tracks total tokens and per-agent usage between calls.
- Computes `delta` as tokens used since the last invocation and appends it
  to the usage history. A flag records whether any positive usage has been
  seen.
- Maintains per-agent histories and extracts the maximum per-agent
  delta `a_t` and mean `\bar{a}_t` over the last ten non-zero samples.
- From the global history it derives the latest usage `u_t` and the mean
  `\bar{u}_t` over the last ten non-zero samples.
- If the most recent ten deltas are all zero, the function returns `1` when
  positive usage was seen previously and otherwise leaves the budget
  unchanged.
- Otherwise it sets the new budget to
  `max(ceil(max(u_t, \bar{u}_t, a_t, \bar{a}_t) * (1 + margin)), 1)`.
- Budgets never drop below one token.

## Tests
Unit tests in `tests/unit/test_metrics_token_budget_spec.py` exercise:
- Threshold adaptation based on prompt history.
- Convergence to `ceil(u * (1 + margin))` for constant workloads.
- Enforcement of the minimum budget of one token after idle periods.
