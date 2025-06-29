"""
Metrics collection for orchestration system.
"""

from typing import Dict, Any, List, Tuple
import time

from prometheus_client import Counter

QUERY_COUNTER = Counter(
    "autoresearch_queries_total", "Total number of queries processed"
)
ERROR_COUNTER = Counter(
    "autoresearch_errors_total", "Total number of errors during processing"
)
TOKENS_IN_COUNTER = Counter(
    "autoresearch_tokens_in_total", "Total input tokens processed"
)
TOKENS_OUT_COUNTER = Counter(
    "autoresearch_tokens_out_total", "Total output tokens produced"
)
EVICTION_COUNTER = Counter(
    "autoresearch_duckdb_evictions_total",
    "Total nodes evicted from RAM to DuckDB",
)


def _get_system_usage() -> Tuple[float, float]:
    """Return current CPU percent and memory usage in MB."""
    try:
        import psutil  # type: ignore

        cpu = psutil.cpu_percent(interval=None)
        mem_mb = psutil.Process().memory_info().rss / (1024 * 1024)
        return cpu, mem_mb
    except Exception:
        return 0.0, 0.0


def record_query() -> None:
    """Increment the global query counter."""
    QUERY_COUNTER.inc()


class OrchestrationMetrics:
    """Collects metrics during query execution."""

    def __init__(self) -> None:
        self.agent_timings: Dict[str, List[float]] = {}
        self.token_counts: Dict[str, Dict[str, int]] = {}
        self.cycle_durations: List[float] = []
        self.error_counts: Dict[str, int] = {}
        self.last_cycle_start: float | None = None
        self.resource_usage: List[Tuple[float, float, float]] = []

    def start_cycle(self) -> None:
        """Mark the start of a new cycle."""
        self.last_cycle_start = time.time()

    def end_cycle(self) -> None:
        """Mark the end of a cycle and record duration."""
        if self.last_cycle_start:
            duration = time.time() - self.last_cycle_start
            self.cycle_durations.append(duration)
            self.last_cycle_start = None

    def record_agent_timing(self, agent_name: str, duration: float) -> None:
        """Record execution time for an agent."""
        if agent_name not in self.agent_timings:
            self.agent_timings[agent_name] = []
        self.agent_timings[agent_name].append(duration)

    def record_system_resources(self) -> None:
        """Record current CPU and memory usage."""
        cpu, mem = _get_system_usage()
        self.resource_usage.append((time.time(), cpu, mem))

    def record_tokens(self, agent_name: str, tokens_in: int, tokens_out: int) -> None:
        """Record token usage for an agent."""
        if agent_name not in self.token_counts:
            self.token_counts[agent_name] = {"in": 0, "out": 0}
        self.token_counts[agent_name]["in"] += tokens_in
        self.token_counts[agent_name]["out"] += tokens_out
        TOKENS_IN_COUNTER.inc(tokens_in)
        TOKENS_OUT_COUNTER.inc(tokens_out)

    def record_error(self, agent_name: str) -> None:
        """Record an error for an agent."""
        if agent_name not in self.error_counts:
            self.error_counts[agent_name] = 0
        self.error_counts[agent_name] += 1
        ERROR_COUNTER.inc()

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        total_duration = sum(self.cycle_durations)
        total_tokens_in = sum(tc["in"] for tc in self.token_counts.values())
        total_tokens_out = sum(tc["out"] for tc in self.token_counts.values())
        total_errors = sum(self.error_counts.values())

        return {
            "total_duration_seconds": total_duration,
            "cycles_completed": len(self.cycle_durations),
            "avg_cycle_duration_seconds": total_duration
            / max(1, len(self.cycle_durations)),
            "total_tokens": {
                "input": total_tokens_in,
                "output": total_tokens_out,
                "total": total_tokens_in + total_tokens_out,
            },
            "agent_timings": self.agent_timings,
            "agent_tokens": self.token_counts,
            "errors": {"total": total_errors, "by_agent": self.error_counts},
            "resource_usage": [
                {
                    "timestamp": ts,
                    "cpu_percent": cpu,
                    "memory_mb": mem,
                }
                for ts, cpu, mem in self.resource_usage
            ],
        }
