import pytest

from autoresearch.data_analysis import metrics_dataframe


# Spec: docs/specs/data-analysis.md#polars-enabled
def test_metrics_dataframe_enabled():
    pytest.importorskip("polars")
    metrics = {"agent_timings": {"A": [1.0, 2.0], "B": [3.0]}}
    df = metrics_dataframe(metrics, polars_enabled=True)
    assert df.shape == (2, 3)
    assert set(df.columns) == {"agent", "avg_time", "count"}


# Spec: docs/specs/data-analysis.md#polars-disabled
def test_metrics_dataframe_disabled():
    metrics = {"agent_timings": {"A": [1.0]}}
    with pytest.raises(RuntimeError):
        metrics_dataframe(metrics, polars_enabled=False)
