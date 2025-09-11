"""Tests for the analysis optional extra."""

from __future__ import annotations

import pytest

from autoresearch.data_analysis import metrics_dataframe


@pytest.mark.requires_analysis
def test_metrics_dataframe_polars() -> None:
    """The analysis extra enables Polars-based metrics summaries."""
    metrics = {"agent_timings": {"agent": [1.0, 2.0, 3.0]}}
    df = metrics_dataframe(metrics, polars_enabled=True)
    assert df["avg_time"][0] == pytest.approx(2.0)
