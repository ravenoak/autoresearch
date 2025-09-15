import pytest

from tests.optional_imports import import_or_skip

from autoresearch.data_analysis import metrics_dataframe


# Spec: docs/specs/data-analysis.md#polars-enabled
@pytest.mark.requires_analysis
def test_metrics_dataframe_enabled() -> None:
    import_or_skip("polars")
    metrics = {"agent_timings": {"A": [1.0, 2.0], "B": [3.0]}}
    df = metrics_dataframe(metrics, polars_enabled=True)
    assert df.shape == (2, 3)
    assert set(df.columns) == {"agent", "avg_time", "count"}


# Spec: docs/specs/data-analysis.md#polars-disabled
def test_metrics_dataframe_disabled() -> None:
    metrics = {"agent_timings": {"A": [1.0]}}
    with pytest.raises(RuntimeError):
        metrics_dataframe(metrics, polars_enabled=False)


def test_metrics_dataframe_polars_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    metrics = {"agent_timings": {"A": [1.0]}}
    monkeypatch.setattr("autoresearch.data_analysis.pl", None)
    with pytest.raises(RuntimeError):
        metrics_dataframe(metrics, polars_enabled=True)
