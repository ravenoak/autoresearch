"""Background resource usage monitoring utilities."""

from __future__ import annotations

import threading
import time
from typing import Optional, List, Dict

import structlog
from prometheus_client import Gauge, start_http_server, CollectorRegistry, REGISTRY

from .orchestration import metrics as orch_metrics


_DEF_REGISTRY = REGISTRY


def _get_usage() -> tuple[float, float]:
    """Return CPU percent and memory usage in MB."""
    try:
        import psutil  # type: ignore

        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.Process().memory_info().rss / (1024 * 1024)
        return cpu, mem
    except Exception:
        return 0.0, 0.0


class ResourceMonitor:
    """Continuously track CPU and memory usage."""

    def __init__(
        self,
        interval: float = 1.0,
        *,
        registry: CollectorRegistry | None = None,
        logger: Optional[structlog.BoundLogger] = None,
    ) -> None:
        self.interval = interval
        self.registry = registry or _DEF_REGISTRY
        self.logger = logger or structlog.get_logger(__name__)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.records: List[Dict[str, float]] = []

        self.cpu_gauge = Gauge(
            "autoresearch_cpu_percent",
            "Process CPU usage percent",
            registry=self.registry,
        )
        self.mem_gauge = Gauge(
            "autoresearch_memory_mb",
            "Process memory usage in MB",
            registry=self.registry,
        )
        self.tokens_in_gauge = Gauge(
            "autoresearch_tokens_in",
            "Total input tokens processed",
            registry=self.registry,
        )
        self.tokens_out_gauge = Gauge(
            "autoresearch_tokens_out",
            "Total output tokens produced",
            registry=self.registry,
        )

    def start(self, prometheus_port: int | None = None) -> None:
        """Start monitoring in a background thread."""
        if self._thread is not None:
            return
        if prometheus_port is not None:
            start_http_server(prometheus_port, registry=self.registry)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            cpu, mem = _get_usage()
            tokens_in = orch_metrics.TOKENS_IN_COUNTER._value.get()
            tokens_out = orch_metrics.TOKENS_OUT_COUNTER._value.get()

            self.cpu_gauge.set(cpu)
            self.mem_gauge.set(mem)
            self.tokens_in_gauge.set(tokens_in)
            self.tokens_out_gauge.set(tokens_out)

            self.logger.info(
                "resource_usage",
                cpu_percent=cpu,
                memory_mb=mem,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
            )
            self.records.append(
                {
                    "timestamp": time.time(),
                    "cpu_percent": cpu,
                    "memory_mb": mem,
                    "tokens_in": tokens_in,
                    "tokens_out": tokens_out,
                }
            )
            time.sleep(self.interval)

    def stop(self) -> None:
        """Stop monitoring."""
        self._stop.set()
        if self._thread:
            self._thread.join()
            self._thread = None

    def get_records(self) -> List[Dict[str, float]]:
        """Return collected resource records."""
        return list(self.records)
