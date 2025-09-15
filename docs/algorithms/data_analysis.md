# Data analysis

`metrics_dataframe` converts nested agent timings into a Polars data
frame with `agent`, `avg_time`, and `count` columns. It evaluates
`polars_enabled` from configuration and rejects execution when Polars is
disabled so that callers never rely on a missing dependency.

## Invariants

- Every returned row aggregates one agent from the `agent_timings`
  mapping.
- Rows contain arithmetic means, not medians or sums, preserving the
  interpretation of latency measurements.
- Empty timing lists are ignored, ensuring the result reflects only
  observed work.
- When no agent reports timings the function returns an empty frame with
  the expected schema, preventing downstream index errors.

## Proof sketch

For each agent key the implementation collects the count and arithmetic
mean of its timing samples. Dividing by the length of the list enforces
the invariant that

\[
\text{avg\_time} = \frac{\sum_{t \in T_a} t}{|T_a|}
\]

for timings `T_a`. Empty lists never enter the accumulator, so the
denominator is non-zero. The constructor builds a Polars frame from the
rows and thus maintains the schema `(agent: str, avg_time: float,
count: int)`.

## Simulation

- `uv run scripts/avg_timing_simulation.py` fabricates agent timings,
  runs `metrics_dataframe`, and confirms the averages `[1.5, 3.0]` for
  two agents.
- [`tests/unit/test_data_analysis.py`](../../tests/unit/test_data_analysis.py)
  checks runtime errors when Polars is disabled and validates the empty
  frame contract.
- [`tests/unit/test_data_analysis_polars.py`](../../tests/unit/test_data_analysis_polars.py)
  exercises successful paths with Polars enabled and verifies column
  ordering.

## Related Issues

- [Add proofs for unverified modules](../../issues/archive/add-proofs-for-unverified-modules.md)
