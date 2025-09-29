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
    time.sleep(0.001)
    monitor.stop()

    assert registry.get_sample_value("autoresearch_system_cpu_percent") == 12.0
    assert registry.get_sample_value("autoresearch_system_memory_percent") == 34.0


def test_collect_returns_expected_dict(monkeypatch):
    monkeypatch.setattr(psutil, "cpu_percent", lambda interval=None: "55.0")
    mem = type("mem", (), {"percent": "44.0"})()
    monkeypatch.setattr(psutil, "virtual_memory", lambda: mem)
    data = SystemMonitor.collect()
    assert data == {"cpu_percent": 55.0, "memory_percent": 44.0}


def test_collect_handles_failures(monkeypatch):
    calls: dict[str, int] = {"cpu": 0, "mem": 0}

    def cpu_percent(interval=None):
        calls["cpu"] += 1
        raise RuntimeError("boom")

    class BrokenMem:
        def __getattr__(self, name: str) -> float:
            calls["mem"] += 1
            raise AttributeError(name)

    monkeypatch.setattr(psutil, "cpu_percent", cpu_percent)
    monkeypatch.setattr(psutil, "virtual_memory", lambda: BrokenMem())

    data = SystemMonitor.collect()
    assert data == {"cpu_percent": 0.0, "memory_percent": 0.0}
    assert calls == {"cpu": 1, "mem": 1}
