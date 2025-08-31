# Data analysis

Metrics aggregation converts nested timing measurements into a tabular view.
`metrics_dataframe` builds a table from agent timings, computing mean
runtime and count per agent. The function relies on the optional
[Polars](https://pola.rs) library. When enabled, it returns a
`polars.DataFrame` with `agent`, `avg_time`, and `count`. If Polars is
disabled or missing, a `RuntimeError` is raised. See the
[specification](../specs/data-analysis.md) for full details.
