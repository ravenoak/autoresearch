from __future__ import annotations

import math
import threading
import time
from typing import Any, Dict, Optional

import psutil
from prometheus_client import REGISTRY, CollectorRegistry, Gauge


def _coerce_float(value: Any) -> float:
    """Return ``value`` converted to ``float`` with NaN/inf protection."""

    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(result):
        return 0.0
    return result


def _gauge(name: str, description: str, registry: CollectorRegistry) -> Gauge:
    """Return a registry-bound gauge, resetting its value if reused."""
    try:
        gauge = Gauge(name, description, registry=registry)
    except ValueError:
        existing = registry._names_to_collectors.get(name)
        if not isinstance(existing, Gauge):  # pragma: no cover - defensive
            raise
        gauge = existing
    gauge.set(0)
    return gauge


class SystemMonitor:
    """Periodically collect system metrics using psutil."""

    def __init__(
        self,
        interval: float = 1.0,
        *,
        registry: CollectorRegistry | None = None,
    ) -> None:
        self.interval = interval
        self.registry = registry or REGISTRY
        self.cpu_gauge = _gauge(
            "autoresearch_system_cpu_percent",
            "System wide CPU usage percent",
            registry=self.registry,
        )
        self.mem_gauge = _gauge(
            "autoresearch_system_memory_percent",
            "System memory usage percent",
            registry=self.registry,
        )
        self.metrics: Dict[str, float] = {}
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            self.metrics = self.collect()
            self.cpu_gauge.set(self.metrics.get("cpu_percent", 0.0))
            self.mem_gauge.set(self.metrics.get("memory_percent", 0.0))
            time.sleep(self.interval)

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join()
            self._thread = None

    @staticmethod
    def collect() -> Dict[str, float]:
        cpu_value: float = 0.0
        mem_percent: float = 0.0

        try:
            cpu_raw = psutil.cpu_percent(interval=None)
            cpu_value = _coerce_float(cpu_raw)
        except Exception:
            cpu_value = 0.0

        try:
            mem = psutil.virtual_memory()
            mem_percent = _coerce_float(getattr(mem, "percent", 0.0))
        except Exception:
            mem_percent = 0.0

        return {
            "cpu_percent": cpu_value,
            "memory_percent": mem_percent,
        }
