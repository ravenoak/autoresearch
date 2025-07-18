import time
from prometheus_client import CollectorRegistry
import psutil
from autoresearch.monitor.system_monitor import SystemMonitor


def test_system_monitor_collects(monkeypatch):
    monkeypatch.setattr(psutil, "cpu_percent", lambda interval=None: 12.0)
    mem = type("mem", (), {"percent": 34.0})()
    monkeypatch.setattr(psutil, "virtual_memory", lambda: mem)

    registry = CollectorRegistry()
    monitor = SystemMonitor(interval=0.01, registry=registry)
    monitor.start()
    time.sleep(0.03)
    monitor.stop()

    assert registry.get_sample_value("autoresearch_system_cpu_percent") == 12.0
    assert registry.get_sample_value("autoresearch_system_memory_percent") == 34.0
