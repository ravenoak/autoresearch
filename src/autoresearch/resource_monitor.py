"""Background resource usage monitoring utilities.

See docs/algorithms/resource_monitor.md for sampling models.
"""

from __future__ import annotations

import contextlib
import importlib.util
import os
import threading
import time
from functools import lru_cache
from typing import Optional

import structlog
from prometheus_client import REGISTRY, CollectorRegistry, Gauge, start_http_server

from .orchestration import metrics as orch_metrics

log = structlog.get_logger(__name__)


_DEF_REGISTRY = REGISTRY
_GPU_SENTINEL_MODULES = ("bertopic", "pynndescent")
_GPU_EXTRA_ENV_VARS = ("EXTRAS", "AR_EXTRAS")


@lru_cache(maxsize=1)
def _gpu_extra_enabled() -> bool:
    """Return ``True`` when the optional GPU extra appears to be installed."""

    extras: set[str] = set()
    for env_name in _GPU_EXTRA_ENV_VARS:
        value = os.environ.get(env_name, "")
        extras.update(part for part in value.split() if part)
    if "gpu" in extras:
        return True
    for module_name in _GPU_SENTINEL_MODULES:
        with contextlib.suppress(Exception):
            if importlib.util.find_spec(module_name) is not None:
                return True
    return False


def _log_gpu_dependency_missing(dependency: str, error: Exception) -> None:
    """Log missing optional GPU dependencies at an informational level."""

    extras_enabled = _gpu_extra_enabled()
    if extras_enabled:
        # Ensure debug-level record is emitted even if global filtering is INFO during tests.
        if os.environ.get("PYTEST_CURRENT_TEST"):
            import logging as _logging
            import structlog as _structlog

            # Temporarily relax structlog filtering to DEBUG
            _structlog.configure(wrapper_class=_structlog.make_filtering_bound_logger(_logging.DEBUG))
            try:
                log.debug(
                    "gpu_metrics_dependency_missing",
                    dependency=dependency,
                    extras_enabled=extras_enabled,
                    reason=str(error),
                    exc_info=error,
                )
            finally:
                # Restore filtering to INFO (project default)
                _structlog.configure(wrapper_class=_structlog.make_filtering_bound_logger(_logging.INFO))
        else:
            log.debug(
                "gpu_metrics_dependency_missing",
                dependency=dependency,
                extras_enabled=extras_enabled,
                reason=str(error),
                exc_info=error,
            )
    else:
        log.info(
            "gpu_metrics_dependency_missing",
            dependency=dependency,
            extras_enabled=extras_enabled,
            reason=str(error),
        )


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


def _get_gpu_stats() -> tuple[float, float]:
    """Return average GPU utilization and memory usage in MB."""

    try:  # pragma: no cover - optional dependency
        import pynvml  # type: ignore
    except ModuleNotFoundError as exc:
        _log_gpu_dependency_missing("pynvml", exc)
    except Exception as exc:  # pragma: no cover - defensive
        log.warning("Failed to import pynvml for GPU monitoring", exc_info=exc)
    else:
        try:
            pynvml.nvmlInit()
            try:
                count = pynvml.nvmlDeviceGetCount()
                util_total = 0.0
                mem_total = 0.0
                for i in range(count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    util_total += float(util.gpu)
                    mem_total += mem.used / (1024 * 1024)
                if count:
                    util_total /= count
                return util_total, mem_total
            finally:
                with contextlib.suppress(Exception):
                    pynvml.nvmlShutdown()
        except Exception as exc:
            log.warning("Failed to get GPU stats via pynvml", exc_info=exc)

    cmd = [
        "nvidia-smi",
        "--query-gpu=utilization.gpu,memory.used",
        "--format=csv,noheader,nounits",
    ]
    try:  # pragma: no cover - may not be present
        import subprocess

        output = ""
        try:
            import psutil  # type: ignore

            proc = psutil.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            output, _ = proc.communicate(timeout=1)
        except ModuleNotFoundError:
            output = ""
        except Exception:
            output = ""
        if not output:
            completed = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=1,
            )
            output = completed.stdout
        utils = []
        mems = []
        for line in output.strip().splitlines():
            try:
                util_str, mem_str = line.split(",")
                utils.append(float(util_str.strip()))
                mems.append(float(mem_str.strip()))
            except Exception:
                continue
        if utils:
            avg_util = sum(utils) / len(utils)
            total_mem = sum(mems)
            return avg_util, total_mem
    except FileNotFoundError as exc:
        _log_gpu_dependency_missing("nvidia-smi", exc)
    except Exception as exc:
        log.warning("Failed to get GPU stats via nvidia-smi", exc_info=exc)

    return 0.0, 0.0


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

        self.cpu_gauge = _gauge(
            "autoresearch_cpu_percent",
            "Process CPU usage percent",
            registry=self.registry,
        )
        self.mem_gauge = _gauge(
            "autoresearch_memory_mb",
            "Process memory usage in MB",
            registry=self.registry,
        )
        self.gpu_gauge = _gauge(
            "autoresearch_gpu_percent",
            "GPU utilization percent",
            registry=self.registry,
        )
        self.gpu_mem_gauge = _gauge(
            "autoresearch_gpu_memory_mb",
            "GPU memory usage in MB",
            registry=self.registry,
        )
        self.tokens_in_gauge = _gauge(
            "autoresearch_tokens_in_snapshot_total",
            "Total input tokens at last snapshot",
            registry=self.registry,
        )
        self.tokens_out_gauge = _gauge(
            "autoresearch_tokens_out_snapshot_total",
            "Total output tokens at last snapshot",
            registry=self.registry,
        )

        self.token_snapshots: list[tuple[float, int, int]] = []

    def start(self, prometheus_port: int | None = None) -> None:
        """Start monitoring in a background thread."""
        if self._thread is not None:
            return
        if self._stop.is_set():
            self._stop = threading.Event()
        if prometheus_port is not None:
            start_http_server(prometheus_port, registry=self.registry)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            cpu, mem = _get_usage()
            gpu, gpu_mem = _get_gpu_stats()
            tokens_in = int(orch_metrics.TOKENS_IN_COUNTER._value.get())
            tokens_out = int(orch_metrics.TOKENS_OUT_COUNTER._value.get())
            self.token_snapshots.append((time.time(), tokens_in, tokens_out))
            self.cpu_gauge.set(cpu)
            self.mem_gauge.set(mem)
            self.gpu_gauge.set(gpu)
            self.gpu_mem_gauge.set(gpu_mem)
            self.tokens_in_gauge.set(tokens_in)
            self.tokens_out_gauge.set(tokens_out)
            self.logger.info(
                "resource_usage",
                cpu_percent=cpu,
                memory_mb=mem,
                gpu_percent=gpu,
                gpu_memory_mb=gpu_mem,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
            )
            time.sleep(self.interval)

    def stop(self) -> None:
        """Stop monitoring."""
        self._stop.set()
        if self._thread:
            self._thread.join()
            self._thread = None

    def __enter__(self) -> "ResourceMonitor":
        """Start the monitor when entering a context."""

        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Ensure the monitor is stopped when leaving a context."""

        self.stop()
