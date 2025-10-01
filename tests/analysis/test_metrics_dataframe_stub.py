import importlib
import sys
import types

import pytest


@pytest.mark.requires_analysis
def test_metrics_dataframe_with_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    """metrics_dataframe should build rows when Polars is available."""
    stub_pl = types.SimpleNamespace(DataFrame=lambda rows: rows)
    monkeypatch.setitem(sys.modules, "polars", stub_pl)
    module = importlib.import_module("autoresearch.data_analysis")
    importlib.reload(module)
    metrics = {"agent_timings": {"a": [1, 3]}}
    df = module.metrics_dataframe(metrics, polars_enabled=True)
    assert df[0]["avg_time"] == 2.0
    assert df[0]["count"] == 2
