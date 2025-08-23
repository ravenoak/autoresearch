"""Node health monitoring utilities."""

from __future__ import annotations

import threading
import time
from typing import Optional

from prometheus_client import REGISTRY, CollectorRegistry, Gauge, start_http_server


class NodeHealthMonitor:
    """Expose Prometheus metrics and perform basic health checks."""

    def __init__(
        self,
        *,
        redis_url: str | None = None,
        ray_address: str | None = None,
        port: int | None = 8000,
        interval: float = 5.0,
        registry: CollectorRegistry | None = None,
    ) -> None:
        self.redis_url = redis_url
        self.ray_address = ray_address
        self.port = port
        self.interval = interval
        self.registry = registry or REGISTRY
        self.redis_gauge = Gauge(
            "autoresearch_redis_up",
            "Redis health status (1=up)",
            registry=self.registry,
        )
        self.ray_gauge = Gauge(
            "autoresearch_ray_up",
            "Ray health status (1=up)",
            registry=self.registry,
        )
        self.health_gauge = Gauge(
            "autoresearch_node_health",
            "Overall node health (1=healthy)",
            registry=self.registry,
        )
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start metric server and background checks."""
        if self.port is not None:
            start_http_server(self.port, registry=self.registry)
        if self._thread:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            self.check_once()
            time.sleep(self.interval)

    def stop(self) -> None:
        """Stop background checks."""
        self._stop.set()
        if self._thread:
            self._thread.join()
            self._thread = None

    def check_once(self) -> None:
        """Run health checks a single time and update gauges."""
        redis_up = self._check_redis()
        ray_up = self._check_ray()
        self.redis_gauge.set(1 if redis_up else 0)
        self.ray_gauge.set(1 if ray_up else 0)
        self.health_gauge.set(1 if redis_up and ray_up else 0)

    def _check_redis(self) -> bool:
        if not self.redis_url:
            return True
        try:
            import redis

            client = redis.Redis.from_url(self.redis_url)
            client.ping()
            client.close()
            return True
        except Exception:
            return False

    def _check_ray(self) -> bool:
        if not self.ray_address:
            return True
        try:
            import ray

            ray.init(
                address=self.ray_address,
                ignore_reinit_error=True,
                configure_logging=False,
            )
            ray.cluster_resources()
            ray.shutdown()
            return True
        except Exception:
            try:
                import ray  # pragma: no cover - ensure module exists

                if ray.is_initialized():
                    ray.shutdown()
            except Exception:
                pass
            return False
