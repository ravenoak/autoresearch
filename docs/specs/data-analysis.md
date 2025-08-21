# Data analysis

This spec describes behavior of `metrics_dataframe` for summarizing agent timing metrics.

## Polars enabled
- Returns a `polars.DataFrame` with columns `agent`, `avg_time`, and `count`.
- Computes per-agent average time and count from `agent_timings`.
- Produces an empty DataFrame with the same columns when no timings are provided.

## Polars disabled
- If `analysis.polars_enabled` is false or the `polars` package is missing, `metrics_dataframe` raises `RuntimeError`.

## Traceability

- Modules
  - [src/autoresearch/data_analysis.py][m1]
- Tests
  - [tests/behavior/features/data_analysis.feature][t1]
  - [tests/unit/test_data_analysis.py][t2]
  - [tests/unit/test_kuzu_polars.py][t3]

[m1]: ../../src/autoresearch/data_analysis.py
[t1]: ../../tests/behavior/features/data_analysis.feature
[t2]: ../../tests/unit/test_data_analysis.py
[t3]: ../../tests/unit/test_kuzu_polars.py
