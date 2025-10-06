"""Tests for `ResourceMonitor` start/stop behavior and gauge helper."""

from __future__ import annotations

import time
from prometheus_client import CollectorRegistry

from autoresearch import resource_monitor


def test_gauge_reuse_resets_value() -> None:
    """Calling `_gauge` twice should reset the metric value."""
    registry = CollectorRegistry()
    gauge = resource_monitor._gauge("test_gauge", "desc", registry)
    gauge.set(5)
    resource_monitor._gauge("test_gauge", "desc", registry)
    assert registry.get_sample_value("test_gauge") == 0


def test_resource_monitor_records_stats(monkeypatch) -> None:
    """Monitor thread updates gauges and token snapshots."""
    registry = CollectorRegistry()

    monkeypatch.setattr(resource_monitor, "_get_usage", lambda: (1.0, 2.0))
    monkeypatch.setattr(resource_monitor, "_get_gpu_stats", lambda: (3.0, 4.0))
    monitor = resource_monitor.ResourceMonitor(interval=0.01, registry=registry)
    monitor.start()
    time.sleep(0.05)
    monitor.stop()

    cpu = registry.get_sample_value("autoresearch_cpu_percent")
    mem = registry.get_sample_value("autoresearch_memory_mb")
    gpu = registry.get_sample_value("autoresearch_gpu_percent")
    gpu_mem = registry.get_sample_value("autoresearch_gpu_memory_mb")
    assert (cpu, mem, gpu, gpu_mem) == (1.0, 2.0, 3.0, 4.0)
    assert monitor.token_snapshots
