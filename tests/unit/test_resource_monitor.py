import time
from prometheus_client import CollectorRegistry, generate_latest

from autoresearch.resource_monitor import ResourceMonitor
from autoresearch.orchestration import metrics


def test_resource_monitor_records_token_usage(monkeypatch):
    monkeypatch.setattr("autoresearch.resource_monitor._get_usage", lambda: (1.0, 2.0))
    registry = CollectorRegistry()
    monitor = ResourceMonitor(interval=0.01, registry=registry)

    start_in = metrics.TOKENS_IN_COUNTER._value.get()
    start_out = metrics.TOKENS_OUT_COUNTER._value.get()
    metrics.TOKENS_IN_COUNTER.inc(3)
    metrics.TOKENS_OUT_COUNTER.inc(5)

    monitor.start()
    time.sleep(0.05)
    monitor.stop()

    data = generate_latest(registry).decode()
    assert "autoresearch_tokens_in" in data
    assert "autoresearch_tokens_out" in data

    records = monitor.get_records()
    assert records
    last = records[-1]
    assert last["cpu_percent"] == 1.0
    assert last["memory_mb"] == 2.0
    assert last["tokens_in"] >= start_in + 3
    assert last["tokens_out"] >= start_out + 5
