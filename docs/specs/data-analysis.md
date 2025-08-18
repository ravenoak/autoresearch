# Data analysis

This spec describes behavior of `metrics_dataframe` for summarizing agent timing metrics.

## Polars enabled
- Returns a `polars.DataFrame` with columns `agent`, `avg_time`, and `count`.
- Computes per-agent average time and count from `agent_timings`.
- Produces an empty DataFrame with the same columns when no timings are provided.

## Polars disabled
- If `analysis.polars_enabled` is false or the `polars` package is missing, `metrics_dataframe` raises `RuntimeError`.
