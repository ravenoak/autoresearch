# mypy: ignore-errors
from __future__ import annotations

import time
from dataclasses import dataclass

import psutil
from prometheus_client import CollectorRegistry
from pytest import MonkeyPatch

from autoresearch.monitor.system_monitor import SystemMonitor


@dataclass
class MemoryUsageFloat:
    """Memory usage structure returning a floating percent."""

    percent: float


@dataclass
class MemoryUsageStr:
    """Memory usage structure returning a string percent."""

    percent: str


@dataclass
class MemoryUsageNaN:
    """Memory usage fixture returning NaN to test normalization."""

    percent: float = float("nan")


@dataclass
class BrokenMem:
    """Memory accessor that raises to simulate failures."""

    calls: dict[str, int]

    def __getattr__(self, name: str) -> float:
        self.calls["mem"] += 1
        raise AttributeError(name)


def test_system_monitor_collects(monkeypatch: MonkeyPatch) -> None:
    def cpu_percent(interval: float | None = None) -> float:
        return 12.0

    monkeypatch.setattr(psutil, "cpu_percent", cpu_percent)
    mem = MemoryUsageFloat(percent=34.0)
    monkeypatch.setattr(psutil, "virtual_memory", lambda: mem)

    registry = CollectorRegistry()
    monitor = SystemMonitor(interval=0.01, registry=registry)
    monitor.start()
    time.sleep(0.001)
    monitor.stop()

    assert registry.get_sample_value("autoresearch_system_cpu_percent") == 12.0
    assert registry.get_sample_value("autoresearch_system_memory_percent") == 34.0
    assert monitor.metrics == {"cpu_percent": 12.0, "memory_percent": 34.0}


def test_collect_returns_expected_tuple(monkeypatch: MonkeyPatch) -> None:
    def cpu_percent(interval: float | None = None) -> float:
        return 55.0

    monkeypatch.setattr(psutil, "cpu_percent", cpu_percent)
    mem = MemoryUsageStr(percent="44.0")
    monkeypatch.setattr(psutil, "virtual_memory", lambda: mem)
    data = SystemMonitor.collect()
    assert data == (55.0, 44.0)


def test_collect_handles_failures(monkeypatch: MonkeyPatch) -> None:
    calls: dict[str, int] = {"cpu": 0, "mem": 0}

    def cpu_percent(interval: float | None = None) -> float:
        calls["cpu"] += 1
        raise RuntimeError("boom")

    monkeypatch.setattr(psutil, "cpu_percent", cpu_percent)
    monkeypatch.setattr(psutil, "virtual_memory", lambda: BrokenMem(calls))

    data = SystemMonitor.collect()
    assert data == (0.0, 0.0)
    assert calls == {"cpu": 1, "mem": 1}


def test_collect_normalizes_iterable_values(monkeypatch: MonkeyPatch) -> None:
    def cpu_percent(interval: float | None = None) -> float:
        return 77.5

    monkeypatch.setattr(psutil, "cpu_percent", cpu_percent)
    monkeypatch.setattr(psutil, "virtual_memory", lambda: MemoryUsageNaN())

    cpu, mem = SystemMonitor.collect()
    assert cpu == 77.5
    assert mem == 0.0
