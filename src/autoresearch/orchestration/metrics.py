"""Metrics collection for orchestration system.

The helpers in this module wrap Prometheus primitives with runtime guards so
that private attributes like ``_value`` are accessed through typed utilities
instead of unchecked ``type: ignore`` directives.
"""

import importlib
import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from os import getenv
from pathlib import Path
from typing import TYPE_CHECKING, Any

from prometheus_client import Counter, Histogram
from prometheus_client.metrics import MetricWrapperBase

from autoresearch.token_budget import (
    AgentUsageStats,
    BudgetRouter,
    RoutingDecision,
    round_with_margin,
)

from .circuit_breaker import CircuitBreakerState

if TYPE_CHECKING:  # pragma: no cover
    from ..config.models import ConfigModel
    from .orchestration_utils import ScoutGateDecision

log = logging.getLogger(__name__)

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
KUZU_QUERY_COUNTER = Counter(
    "autoresearch_kuzu_queries_total",
    "Total number of Kuzu queries executed",
)
KUZU_QUERY_TIME = Histogram(
    "autoresearch_kuzu_query_seconds",
    "Time spent executing Kuzu queries",
)


def ensure_counters_initialized() -> None:
    """Ensure global counters are registered without changing their values."""
    QUERY_COUNTER.inc(0)
    TOKENS_IN_COUNTER.inc(0)
    TOKENS_OUT_COUNTER.inc(0)


def _metric_accessor(metric: MetricWrapperBase, attr: str) -> Any | None:
    """Return a typed accessor for a private Prometheus metric attribute."""

    value = getattr(metric, attr, None)
    if value is None:
        return None
    has_set = hasattr(value, "set")
    has_get = hasattr(value, "get")
    if has_set and has_get:
        return value
    return None


def reset_counter(counter: MetricWrapperBase) -> None:
    """Reset a Prometheus counter to zero with runtime guards."""

    accessor = _metric_accessor(counter, "_value")
    if accessor is None:
        return
    try:
        accessor.set(0)
    except Exception:  # pragma: no cover - defensive
        log.debug("Failed to reset counter %s; leaving value unchanged", counter, exc_info=True)


def snapshot_counter(counter: MetricWrapperBase) -> float:
    """Return the current value for ``counter`` if accessible."""

    accessor = _metric_accessor(counter, "_value")
    if accessor is None:
        return 0.0
    try:
        return float(accessor.get())
    except Exception:  # pragma: no cover - defensive
        log.debug("Failed to read counter %s; assuming zero", counter, exc_info=True)
        return 0.0


def restore_counter(counter: MetricWrapperBase, value: float) -> None:
    """Restore ``counter`` to ``value`` if the backing accessor is available."""

    accessor = _metric_accessor(counter, "_value")
    if accessor is None:
        return
    try:
        accessor.set(value)
    except Exception:  # pragma: no cover - defensive
        log.debug(
            "Failed to restore counter %s to snapshot value %s",
            counter,
            value,
            exc_info=True,
        )


def reset_histogram(histogram: Histogram) -> None:
    """Reset histogram aggregates without accessing private attributes unchecked."""

    sum_accessor = _metric_accessor(histogram, "_sum")
    count_accessor = _metric_accessor(histogram, "_count")
    if sum_accessor is not None:
        try:
            sum_accessor.set(0)
        except Exception:  # pragma: no cover - defensive
            log.debug(
                "Failed to reset histogram sum for %s; leaving value unchanged",
                histogram,
                exc_info=True,
            )
    if count_accessor is not None:
        try:
            count_accessor.set(0)
        except Exception:  # pragma: no cover - defensive
            log.debug(
                "Failed to reset histogram count for %s; leaving value unchanged",
                histogram,
                exc_info=True,
            )


def reset_metrics() -> None:
    """Reset all Prometheus counters to zero."""
    counters: list[MetricWrapperBase] = [
        QUERY_COUNTER,
        ERROR_COUNTER,
        TOKENS_IN_COUNTER,
        TOKENS_OUT_COUNTER,
        EVICTION_COUNTER,
        KUZU_QUERY_COUNTER,
    ]
    for counter in counters:
        reset_counter(counter)
    reset_histogram(KUZU_QUERY_TIME)


@contextmanager
def temporary_metrics() -> Iterator[None]:
    """Provide a context where metric counters are restored on exit."""
    counters: list[MetricWrapperBase] = [
        QUERY_COUNTER,
        ERROR_COUNTER,
        TOKENS_IN_COUNTER,
        TOKENS_OUT_COUNTER,
        EVICTION_COUNTER,
        KUZU_QUERY_COUNTER,
    ]
    snapshot = [snapshot_counter(counter) for counter in counters]
    hist_sum_accessor = _metric_accessor(KUZU_QUERY_TIME, "_sum")
    hist_count_accessor = _metric_accessor(KUZU_QUERY_TIME, "_count")
    hist_sum = hist_sum_accessor.get() if hist_sum_accessor is not None else 0
    hist_count = hist_count_accessor.get() if hist_count_accessor is not None else 0
    try:
        yield
    finally:
        for counter, value in zip(counters, snapshot):
            restore_counter(counter, value)
        if hist_sum_accessor is not None:
            try:
                hist_sum_accessor.set(hist_sum)
            except Exception:  # pragma: no cover
                log.debug(
                    "Failed to restore histogram sum for %s", KUZU_QUERY_TIME, exc_info=True
                )
        if hist_count_accessor is not None:
            try:
                hist_count_accessor.set(hist_count)
            except Exception:  # pragma: no cover
                log.debug(
                    "Failed to restore histogram count for %s",
                    KUZU_QUERY_TIME,
                    exc_info=True,
                )


def _get_system_usage() -> tuple[float, float, float, float]:  # noqa: E302
    """Return CPU, memory, GPU utilization, and GPU memory in MB."""

    try:
        import psutil
    except Exception:
        log.debug(
            "psutil unavailable; returning zero system usage metrics",
            exc_info=True,
        )
        return 0.0, 0.0, 0.0, 0.0

    cpu_percent = psutil.cpu_percent(interval=None)
    cpu = float(cpu_percent if isinstance(cpu_percent, (int, float)) else 0.0)
    mem_info = psutil.Process().memory_info()
    mem_mb = float(mem_info.rss) / (1024 * 1024)

    gpu_util = 0.0
    gpu_mem = 0.0
    try:
        pynvml_module = importlib.import_module("pynvml")
    except Exception:  # pragma: no cover - optional dependency
        log.debug(
            "pynvml unavailable; GPU metrics default to zero",
            exc_info=True,
        )
        return cpu, mem_mb, gpu_util, gpu_mem

    def _coerce_to_float(value: object) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, list) and value and isinstance(value[0], (int, float)):
            return float(value[0])
        return 0.0

    try:
        pynvml_module.nvmlInit()
        count = int(pynvml_module.nvmlDeviceGetCount())
        for index in range(count):
            handle = pynvml_module.nvmlDeviceGetHandleByIndex(index)
            utilization = pynvml_module.nvmlDeviceGetUtilizationRates(handle)
            memory = pynvml_module.nvmlDeviceGetMemoryInfo(handle)
            gpu_value = _coerce_to_float(getattr(utilization, "gpu", 0.0))
            gpu_util += gpu_value
            gpu_mem += _coerce_to_float(getattr(memory, "used", 0.0)) / (1024 * 1024)
        if count:
            gpu_util /= count
    except Exception:  # pragma: no cover - optional dependency
        log.debug(
            "Failed to collect GPU metrics via pynvml; defaults applied",
            exc_info=True,
        )
        gpu_util = 0.0
        gpu_mem = 0.0
    finally:
        with suppress(Exception):
            pynvml_module.nvmlShutdown()

    return cpu, mem_mb, gpu_util, gpu_mem


def record_query() -> None:
    """Increment the global query counter."""
    QUERY_COUNTER.inc()


def _mean_last_nonzero(values: list[int], n: int = 10) -> float:
    """Return the mean of the last ``n`` positive entries in ``values``.

    Parameters
    ----------
    values:
        Sequence of token deltas.
    n:
        Maximum number of non-zero samples to average.

    Returns
    -------
    float
        Mean of the last ``n`` non-zero values or ``0.0`` if none exist.
    """

    total = 0
    count = 0
    for v in reversed(values):
        if v > 0:
            total += v
            count += 1
            if count == n:
                break
    return total / count if count else 0.0


def _mean_last(values: list[int], n: int = 10) -> float:
    """Return the mean of the last ``n`` entries in ``values``.

    Unlike :func:`_mean_last_nonzero`, zeros are included so the mean
    reflects periods where an agent produced no tokens.

    Parameters
    ----------
    values:
        Sequence of token deltas.
    n:
        Maximum number of samples to average.

    Returns
    -------
    float
        Mean of the last ``n`` values or ``0.0`` if ``values`` is empty.
    """

    recent = values[-n:]
    return sum(recent) / len(recent) if recent else 0.0


class OrchestrationMetrics:
    """Collects metrics during query execution."""

    def __init__(self) -> None:
        self.agent_timings: dict[str, list[float]] = {}
        self.token_counts: dict[str, dict[str, int]] = {}
        self.cycle_durations: list[float] = []
        self.error_counts: dict[str, int] = {}
        self.last_cycle_start: float | None = None
        self.resource_usage: list[tuple[float, float, float, float, float]] = []
        self.release = getenv("AUTORESEARCH_RELEASE", "development")
        self._release_logged = False
        self.prompt_lengths: list[int] = []
        self.token_usage_history: list[int] = []
        self._last_total_tokens = 0
        self._ever_used_tokens = False
        self.agent_usage_history: dict[str, list[int]] = {}
        self._last_agent_totals: dict[str, int] = {}
        self.circuit_breakers: dict[str, CircuitBreakerState] = {}
        self.gate_events: list[dict[str, Any]] = []
        self.agent_token_samples: dict[str, list[tuple[int, int]]] = {}
        self._max_sample_history = 20
        self.routing_decisions: list[RoutingDecision] = []

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
        timings = self.agent_timings[agent_name]
        timings.append(duration)
        if len(timings) > self._max_sample_history:
            del timings[0 : len(timings) - self._max_sample_history]
        latency_ms = duration * 1000.0
        avg_ms = sum(timings) * 1000.0 / len(timings)
        log.info(
            "Recorded agent latency sample",
            extra={
                "agent": agent_name,
                "latency_ms": latency_ms,
                "avg_latency_ms": avg_ms,
                "samples": len(timings),
            },
        )

    def record_system_resources(self) -> None:
        """Record current CPU, memory, and GPU usage."""
        cpu, mem, gpu, gpu_mem = _get_system_usage()
        self.resource_usage.append((time.time(), cpu, mem, gpu, gpu_mem))

    def record_tokens(self, agent_name: str, tokens_in: int, tokens_out: int) -> None:
        """Record token usage for an agent."""
        if agent_name not in self.token_counts:
            self.token_counts[agent_name] = {"in": 0, "out": 0}
        self.token_counts[agent_name]["in"] += tokens_in
        self.token_counts[agent_name]["out"] += tokens_out
        TOKENS_IN_COUNTER.inc(tokens_in)
        TOKENS_OUT_COUNTER.inc(tokens_out)
        samples = self.agent_token_samples.setdefault(agent_name, [])
        samples.append((tokens_in, tokens_out))
        if len(samples) > self._max_sample_history:
            del samples[0 : len(samples) - self._max_sample_history]
        avg_tokens = sum(sum(pair) for pair in samples) / len(samples)
        log.info(
            "Recorded agent token usage",
            extra={
                "agent": agent_name,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "avg_tokens_per_call": avg_tokens,
                "samples": len(samples),
            },
        )

    def record_error(self, agent_name: str) -> None:
        """Record an error for an agent."""
        if agent_name not in self.error_counts:
            self.error_counts[agent_name] = 0
        self.error_counts[agent_name] += 1
        ERROR_COUNTER.inc()

    def record_circuit_breaker(
        self, agent_name: str, state: CircuitBreakerState
    ) -> None:
        """Record the circuit breaker ``state`` for ``agent_name``."""
        self.circuit_breakers[agent_name] = state

    def record_gate_decision(self, decision: "ScoutGateDecision") -> None:
        """Record the scout gate ``decision`` for telemetry and analysis."""

        event = {
            "should_debate": decision.should_debate,
            "target_loops": decision.target_loops,
            "heuristics": decision.heuristics,
            "thresholds": decision.thresholds,
            "reason": decision.reason,
            "tokens_saved_estimate": decision.tokens_saved,
        }
        self.gate_events.append(event)

    def _log_release_tokens(self) -> None:
        """Persist token counts for this release."""
        if self._release_logged:
            return
        import json

        path = Path(
            getenv(
                "AUTORESEARCH_RELEASE_METRICS",
                "tests/integration/baselines/release_tokens.json",
            )
        )
        data: dict[str, Any] = {}
        if path.exists():
            try:
                data = json.loads(path.read_text())
            except Exception:
                log.debug(
                    "Failed to read release metrics from %s; starting fresh",
                    path,
                    exc_info=True,
                )
                data = {}
        data[self.release] = self.token_counts
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
        self._release_logged = True

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all metrics."""
        total_duration = sum(self.cycle_durations)
        total_tokens_in = sum(tc["in"] for tc in self.token_counts.values())
        total_tokens_out = sum(tc["out"] for tc in self.token_counts.values())
        total_errors = sum(self.error_counts.values())

        self._log_release_tokens()

        latency_summary: dict[str, float] = {}
        avg_tokens_summary: dict[str, float] = {}
        for agent, samples in self.agent_token_samples.items():
            latencies = [
                duration * 1000.0 for duration in self.agent_timings.get(agent, [])
            ]
            stats = AgentUsageStats.from_samples(samples, latencies)
            if stats is None:
                continue
            latency_summary[agent] = stats.p95_latency_ms
            avg_tokens_summary[agent] = stats.avg_total_tokens

        savings_by_agent: dict[str, float] = {}
        for decision in self.routing_decisions:
            savings = decision.cost_savings()
            if savings is None:
                continue
            savings_by_agent.setdefault(decision.agent, 0.0)
            savings_by_agent[decision.agent] += savings
        total_savings = sum(savings_by_agent.values())

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
            "circuit_breakers": self.circuit_breakers,
            "gate_events": self.gate_events,
            "resource_usage": [
                {
                    "timestamp": ts,
                    "cpu_percent": cpu,
                    "memory_mb": mem,
                    "gpu_percent": gpu,
                    "gpu_memory_mb": gpu_mem,
                }
                for ts, cpu, mem, gpu, gpu_mem in self.resource_usage
            ],
            "agent_latency_p95_ms": latency_summary,
            "agent_avg_tokens": avg_tokens_summary,
            "model_routing_decisions": [
                decision.to_dict() for decision in self.routing_decisions
            ],
            "model_routing_cost_savings": {
                "total": total_savings,
                "by_agent": savings_by_agent,
            },
        }

    def get_agent_usage_stats(
        self, agent_name: str, default_latency_ms: float
    ) -> AgentUsageStats | None:
        """Return rolling usage statistics for ``agent_name`` when available."""

        samples = self.agent_token_samples.get(agent_name)
        if not samples:
            return None
        latencies = [
            duration * 1000.0 for duration in self.agent_timings.get(agent_name, [])
        ]
        stats = AgentUsageStats.from_samples(samples, latencies)
        if stats is None:
            return None
        if stats.p95_latency_ms <= 0 and default_latency_ms > 0:
            return AgentUsageStats(
                avg_prompt_tokens=stats.avg_prompt_tokens,
                avg_completion_tokens=stats.avg_completion_tokens,
                p95_latency_ms=default_latency_ms,
                call_count=stats.call_count,
            )
        return stats

    def _default_token_share(self, config: "ConfigModel", agent_name: str) -> float:
        """Return an even token share when the agent does not override it."""

        agents = getattr(config, "agents", [])
        if not agents:
            return 1.0
        return 1.0 / max(len(agents), 1)

    def apply_model_routing(self, agent_name: str, config: "ConfigModel") -> str | None:
        """Update ``config`` with a budget-aware model recommendation."""

        routing_cfg = getattr(config, "model_routing", None)
        if (
            routing_cfg is None
            or not routing_cfg.enabled
            or not routing_cfg.model_profiles
        ):
            return None

        agent_cfg = config.agent_config.get(agent_name)
        preferred = agent_cfg.preferred_models if agent_cfg else None
        allowed = agent_cfg.allowed_models if agent_cfg else None
        if preferred is not None and len(preferred) == 0:
            preferred = None
        if allowed is not None and len(allowed) == 0:
            allowed = None
        latency_slo = agent_cfg.latency_slo_ms if agent_cfg else None
        current_model = (
            agent_cfg.model if agent_cfg and agent_cfg.model else config.default_model
        )

        token_share = agent_cfg.token_share if agent_cfg else None
        if token_share is None:
            token_share = self._default_token_share(config, agent_name)
        else:
            token_share = max(0.0, min(float(token_share), 1.0))

        agent_budget_tokens = None
        if config.token_budget is not None:
            agent_budget_tokens = max(config.token_budget * token_share, 0.0)

        usage = self.get_agent_usage_stats(
            agent_name, routing_cfg.default_latency_slo_ms
        )
        router = BudgetRouter(
            routing_cfg.model_profiles,
            default_model=config.default_model,
            pressure_ratio=routing_cfg.budget_pressure_ratio,
            default_latency_slo_ms=routing_cfg.default_latency_slo_ms,
        )
        decision = router.select_model_decision(
            agent_name,
            usage,
            agent_budget_tokens=agent_budget_tokens,
            agent_latency_slo_ms=latency_slo,
            allowed_models=allowed,
            preferred_models=preferred,
            current_model=current_model,
        )
        self.routing_decisions.append(decision)
        selected = decision.selected_model
        if not selected or selected == current_model:
            return selected

        from ..config.models import AgentConfig  # Local import to avoid cycles

        agent_cfg_obj = agent_cfg or config.agent_config.setdefault(
            agent_name, AgentConfig()
        )
        agent_cfg_obj.model = selected
        log.info("Applied budget-aware model routing", extra=decision.as_log_extra())
        return selected

    # ------------------------------------------------------------------
    # Query token monitoring helpers
    # ------------------------------------------------------------------

    def _total_tokens(self) -> int:
        """Return the total tokens used in the current run."""

        total = 0
        for counts in self.token_counts.values():
            inbound = int(counts.get("in", 0))
            outbound = int(counts.get("out", 0))
            total += inbound + outbound
        return total

    def record_query_tokens(self, query: str, path: Path | None = None) -> None:
        """Persist total token usage for ``query``.

        The metrics are appended to ``path`` which defaults to the
        ``AUTORESEARCH_QUERY_TOKENS`` environment variable or
        ``tests/integration/baselines/query_tokens.json``.
        """
        import json

        if path is None:
            path = Path(
                getenv(
                    "AUTORESEARCH_QUERY_TOKENS",
                    "tests/integration/baselines/query_tokens.json",
                )
            )

        data: dict[str, int] = {}
        if path.exists():
            try:
                data = json.loads(path.read_text())
            except Exception:
                log.debug(
                    "Failed to read token metrics from %s; starting fresh",
                    path,
                    exc_info=True,
                )
                data = {}

        data[query] = self._total_tokens()
        path.write_text(json.dumps(data, indent=2))

    def check_query_regression(
        self, query: str, baseline_path: Path, threshold: int = 0
    ) -> bool:
        """Return ``True`` if token usage exceeds the baseline."""
        import json

        if not baseline_path.exists():
            return False
        try:
            baseline = json.loads(baseline_path.read_text())
        except Exception:
            log.debug(
                "Failed to read baseline tokens from %s; assuming no regression",
                baseline_path,
                exc_info=True,
            )
            return False
        baseline_total = baseline.get(query)
        if not isinstance(baseline_total, (int, float)):
            return False
        total_tokens = self._total_tokens()
        return total_tokens > float(baseline_total) + threshold

    # ------------------------------------------------------------------
    # Heuristics for prompt compression and budget adjustment
    # ------------------------------------------------------------------

    def compress_prompt_if_needed(
        self, prompt: str, token_budget: int, *, threshold: float = 1.0
    ) -> str:
        """Return a compressed prompt when usage exceeds ``token_budget``.

        Parameters
        ----------
        prompt:
            The original prompt text.
        token_budget:
            Maximum allowed tokens for the prompt.
        threshold:
            Fraction of the budget that triggers compression. A value of
            ``1.0`` means the prompt is compressed only when it exceeds the
            budget, while ``0.9`` would compress once 90% of the budget is
            reached.
        """

        tokens = len(prompt.split())
        self.prompt_lengths.append(tokens)
        avg_tokens = sum(self.prompt_lengths) / len(self.prompt_lengths)

        adjusted_threshold = threshold
        if avg_tokens > token_budget:
            adjusted_threshold = min(threshold, token_budget / avg_tokens)

        if tokens <= int(token_budget * adjusted_threshold):
            return prompt

        from ..llm.token_counting import compress_prompt

        return compress_prompt(prompt, token_budget)

    def suggest_token_budget(self, current_budget: int, *, margin: float = 0.1) -> int:
        """Return an adjusted token budget based on recorded usage.

        ``margin`` controls how aggressively the budget adapts. The
        calculation considers the most recent per-cycle usage, per-agent
        historical averages (which include zero-use cycles), and the
        overall average across the last ten non-zero samples. If no usage
        has been observed, the budget
        remains unchanged. A window of only zero-usage samples drives the
        budget to one token. When usage stabilizes, the update converges to
        ``round(u * (1 + margin))`` for constant usage ``u`` using
        round-half-up semantics so ``.5`` cases round upward. Negative
        ``margin`` values are treated as zero.

        See ``docs/algorithms/token_budgeting.md`` for derivation and a
        formal proof of convergence.
        """

        margin = max(margin, 0.0)

        total = self._total_tokens()
        delta = total - self._last_total_tokens
        self._last_total_tokens = total
        if delta > 0:
            self._ever_used_tokens = True
        self.token_usage_history.append(delta)

        recent_usage = self.token_usage_history[-10:]
        if all(u == 0 for u in recent_usage):
            if self._ever_used_tokens:
                return 1
            return current_budget

        avg_used = _mean_last_nonzero(self.token_usage_history)
        latest = recent_usage[-1]

        max_agent_delta = 0
        max_agent_avg = 0.0
        for name, counts in self.token_counts.items():
            total_agent = counts.get("in", 0) + counts.get("out", 0)
            last = self._last_agent_totals.get(name, 0)
            agent_delta = total_agent - last
            self._last_agent_totals[name] = total_agent
            history = self.agent_usage_history.setdefault(name, [])
            history.append(agent_delta)
            agent_avg = _mean_last(history)
            if agent_delta > max_agent_delta:
                max_agent_delta = agent_delta
            if agent_avg > max_agent_avg:
                max_agent_avg = agent_avg

        usage_candidates = [latest, avg_used, max_agent_delta, max_agent_avg]

        desired = round_with_margin(max(usage_candidates), margin)

        return max(desired, 1)
