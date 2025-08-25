from types import SimpleNamespace

from autoresearch.orchestration import metrics


def test_reset_metrics():
    metrics.QUERY_COUNTER.inc(3)
    metrics.reset_metrics()
    assert metrics.QUERY_COUNTER._value.get() == 0


def test_temporary_metrics_restores_state(monkeypatch):
    metrics.reset_metrics()
    monkeypatch.setattr(
        metrics.KUZU_QUERY_TIME,
        "_count",
        SimpleNamespace(get=lambda: 0, set=lambda v: None),
        raising=False,
    )
    with metrics.temporary_metrics():
        metrics.QUERY_COUNTER.inc()
    assert metrics.QUERY_COUNTER._value.get() == 0


def test_get_system_usage_returns_floats():
    usage = metrics._get_system_usage()
    assert len(usage) == 4
    assert all(isinstance(v, float) for v in usage)
