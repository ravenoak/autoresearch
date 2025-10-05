"""Metrics collection for orchestration system.

The helpers in this module wrap Prometheus primitives with runtime guards so
that private attributes like ``_value`` are accessed through typed utilities
instead of unchecked ``type: ignore`` directives.
"""

import importlib
import json
import logging
import math
import time
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from dataclasses import replace
from os import getenv
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, SupportsFloat

from prometheus_client import Counter, Histogram
from prometheus_client.metrics import MetricWrapperBase

from autoresearch.token_budget import (
    AgentUsageStats,
    BudgetRouter,
    RoutingDecision,
    round_with_margin,
)

from .circuit_breaker import CircuitBreakerState
from .model_routing import (
    RoutingOverrideRequest,
    ingest_state_overrides,
    resolve_agent_directives,
)
from .reasoning_payloads import FrozenReasoningStep

if TYPE_CHECKING:  # pragma: no cover
    from ..config.models import ConfigModel
    from .orchestration_utils import ScoutGateDecision
    from .state import QueryState

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
GRAPH_BUILD_COUNTER = Counter(
    "autoresearch_graph_ingestions_total",
    "Total knowledge graph ingestion runs captured",
)
GRAPH_ENTITY_COUNTER = Counter(
    "autoresearch_graph_entities_total",
    "Total entities processed during graph ingestions",
)
GRAPH_RELATION_COUNTER = Counter(
    "autoresearch_graph_relations_total",
    "Total relations processed during graph ingestions",
)
GRAPH_CONTRADICTION_COUNTER = Counter(
    "autoresearch_graph_contradictions_total",
    "Total contradictions detected during graph ingestions",
)
GRAPH_NEIGHBOR_COUNTER = Counter(
    "autoresearch_graph_neighbor_edges_total",
    "Total neighbor edges exposed to the planner",
)
GRAPH_BUILD_SECONDS = Histogram(
    "autoresearch_graph_ingestion_seconds",
    "Latency of knowledge graph ingestion runs",
)


def ensure_counters_initialized() -> None:
    """Ensure global counters are registered without changing their values."""
    QUERY_COUNTER.inc(0)
    TOKENS_IN_COUNTER.inc(0)
    TOKENS_OUT_COUNTER.inc(0)
    GRAPH_BUILD_COUNTER.inc(0)
    GRAPH_ENTITY_COUNTER.inc(0)
    GRAPH_RELATION_COUNTER.inc(0)
    GRAPH_CONTRADICTION_COUNTER.inc(0)
    GRAPH_NEIGHBOR_COUNTER.inc(0)


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


def _safe_float(value: Any) -> float:
    """Return ``value`` coerced to a finite float when possible."""

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            return _safe_float(item)
        return 0.0
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return 0.0
        try:
            result = float(text)
        except ValueError:
            return 0.0
    elif isinstance(value, SupportsFloat):
        try:
            result = float(value)
        except (TypeError, ValueError):
            return 0.0
    else:
        return 0.0
    if not math.isfinite(result):
        return 0.0
    return result


def _coerce_float(value: Any) -> float:
    """Return ``value`` converted to ``float`` with NaN/inf protection."""

    return _safe_float(value)


def _normalize_latency_mapping(
    payload: Mapping[str, Any] | Sequence[Any] | None,
    *,
    prefix: str = "",
) -> dict[str, float]:
    """Return ``payload`` flattened into non-negative float latencies."""

    result: dict[str, float] = {}
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, Mapping):
                nested = _normalize_latency_mapping(value, prefix=name)
                if nested:
                    result.update(nested)
                else:
                    result[name] = 0.0
                continue
            if isinstance(value, Sequence) and not isinstance(
                value, (str, bytes, bytearray)
            ):
                nested = _normalize_latency_mapping(value, prefix=name)
                if nested:
                    result.update(nested)
                else:
                    result[name] = 0.0
                continue
            result[name] = max(0.0, _safe_float(value))
        return result
    if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
        for index, item in enumerate(payload):
            name = f"{prefix}[{index}]" if prefix else str(index)
            result.update(_normalize_latency_mapping(item, prefix=name))
        return result
    if prefix:
        result[prefix] = max(0.0, _safe_float(payload))
    return result


def _snapshot_value(value: Any) -> Any:
    """Return ``value`` converted to an immutable telemetry-friendly form."""

    if isinstance(value, MappingProxyType):
        return value
    if isinstance(value, FrozenReasoningStep):
        return snapshot_mapping(value.to_dict())
    if isinstance(value, Mapping):
        return snapshot_mapping(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(_snapshot_value(item) for item in value)
    return value


def snapshot_mapping(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return an immutable snapshot of ``payload`` suitable for telemetry.

    Args:
        payload: Mapping to snapshot.

    Returns:
        Mapping proxy containing recursively frozen values.
    """

    if isinstance(payload, FrozenReasoningStep):
        items = payload.to_dict().items()
    else:
        items = payload.items()
    snapshot: dict[str, Any] = {}
    for key, value in items:
        snapshot[str(key)] = _snapshot_value(value)
    return MappingProxyType(snapshot)


def snapshot_reasoning_claims(
    claims: Mapping[str, Any] | Sequence[Any] | None,
) -> tuple[Mapping[str, Any], ...]:
    """Return immutable snapshots for reasoning claims.

    Args:
        claims: Mapping or sequence describing reasoning claims.

    Returns:
        Tuple of mapping proxies for each non-empty claim.
    """

    if claims is None:
        return tuple()
    if isinstance(claims, Mapping):
        frozen = snapshot_mapping(claims)
        return (frozen,) if len(frozen) else tuple()
    if isinstance(claims, Sequence) and not isinstance(claims, (str, bytes, bytearray)):
        frozen_claims: list[Mapping[str, Any]] = []
        for claim in claims:
            if isinstance(claim, Mapping):
                frozen = snapshot_mapping(claim)
                if len(frozen):
                    frozen_claims.append(frozen)
        return tuple(frozen_claims)
    return tuple()


_GRAPH_TOTAL_FIELDS: tuple[str, ...] = (
    "entity_count",
    "relation_count",
    "ingestion_seconds",
    "contradiction_count",
    "contradiction_score",
    "contradiction_weighted",
    "contradiction_weight",
    "neighbor_node_count",
    "neighbor_edge_count",
    "path_count",
    "provenance_count",
    "similarity_score",
    "similarity_weighted",
    "similarity_weight",
)


def _empty_graph_totals() -> dict[str, float]:
    """Return a zero-initialized telemetry mapping for graph aggregates."""

    return {key: 0.0 for key in _GRAPH_TOTAL_FIELDS}


def _accumulate_graph_totals(
    totals: dict[str, float],
    record: Mapping[str, Any],
    *,
    fields: Iterable[str] = _GRAPH_TOTAL_FIELDS,
) -> None:
    """Accumulate ``record`` values into ``totals`` using safe float coercion."""

    for key in fields:
        if key not in totals:
            totals[key] = 0.0
        totals[key] += _coerce_float(record.get(key, 0.0))


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
        GRAPH_BUILD_COUNTER,
        GRAPH_ENTITY_COUNTER,
        GRAPH_RELATION_COUNTER,
        GRAPH_CONTRADICTION_COUNTER,
        GRAPH_NEIGHBOR_COUNTER,
    ]
    for counter in counters:
        reset_counter(counter)
    reset_histogram(KUZU_QUERY_TIME)
    reset_histogram(GRAPH_BUILD_SECONDS)


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
        GRAPH_BUILD_COUNTER,
        GRAPH_ENTITY_COUNTER,
        GRAPH_RELATION_COUNTER,
        GRAPH_CONTRADICTION_COUNTER,
        GRAPH_NEIGHBOR_COUNTER,
    ]
    snapshot = [snapshot_counter(counter) for counter in counters]
    histograms: list[Histogram] = [KUZU_QUERY_TIME, GRAPH_BUILD_SECONDS]
    histogram_snapshots: list[
        tuple[
            Histogram,
            Any | None,
            Any,
            Any | None,
            Any,
        ]
    ] = []
    for histogram in histograms:
        sum_accessor = _metric_accessor(histogram, "_sum")
        count_accessor = _metric_accessor(histogram, "_count")
        sum_value = sum_accessor.get() if sum_accessor is not None else 0
        count_value = count_accessor.get() if count_accessor is not None else 0
        histogram_snapshots.append(
            (histogram, sum_accessor, sum_value, count_accessor, count_value)
        )
    try:
        yield
    finally:
        for counter, value in zip(counters, snapshot):
            restore_counter(counter, value)
        for histogram, sum_accessor, sum_value, count_accessor, count_value in histogram_snapshots:
            if sum_accessor is not None:
                try:
                    sum_accessor.set(sum_value)
                except Exception:  # pragma: no cover
                    log.debug(
                        "Failed to restore histogram sum for %s",
                        histogram,
                        exc_info=True,
                    )
            if count_accessor is not None:
                try:
                    count_accessor.set(count_value)
                except Exception:  # pragma: no cover
                    log.debug(
                        "Failed to restore histogram count for %s",
                        histogram,
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
        self.routing_override_requests: list[RoutingOverrideRequest] = []
        self.routing_strategy: str | None = None
        self.routing_agent_constraints: dict[str, dict[str, float | None]] = {}
        self.routing_agent_recommendations: dict[str, str | None] = {}
        self.graph_ingestions: list[dict[str, Any]] = []
        self.gate_coverage_ratios: list[float] = []
        self.gate_agreement_stats: list[dict[str, Any]] = []
        self.gate_decision_outcomes: list[str] = []

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

    def _register_override(
        self, override: RoutingOverrideRequest
    ) -> RoutingOverrideRequest:
        """Deduplicate and record routing overrides."""

        for existing in self.routing_override_requests:
            if (
                existing.agent.lower() == override.agent.lower()
                and existing.source == override.source
                and existing.reason == override.reason
                and existing.requested_model == override.requested_model
                and existing.threshold == override.threshold
            ):
                return existing
        self.routing_override_requests.append(override)
        log.info("Registered routing override", extra=override.as_log_extra())
        return override

    def request_model_escalation(
        self,
        agent_name: str,
        *,
        model: str | None,
        source: str,
        reason: str,
        confidence: float | None = None,
        threshold: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> RoutingOverrideRequest:
        """Register a routing override triggered by control policies."""

        extra_metadata = dict(metadata) if isinstance(metadata, Mapping) else {}
        override = RoutingOverrideRequest(
            agent=agent_name,
            requested_model=model,
            source=source,
            reason=reason,
            confidence=confidence,
            threshold=threshold,
            metadata=extra_metadata,
        )
        return self._register_override(override)

    def record_gate_decision(self, decision: "ScoutGateDecision") -> None:
        """Record the scout gate ``decision`` for telemetry and analysis."""

        event = {
            "should_debate": decision.should_debate,
            "target_loops": decision.target_loops,
            "heuristics": decision.heuristics,
            "thresholds": decision.thresholds,
            "reason": decision.reason,
            "tokens_saved_estimate": decision.tokens_saved,
            "rationales": decision.rationales,
            "coverage": decision.telemetry.get("coverage"),
            "contradiction_total": decision.telemetry.get("contradiction_total"),
            "contradiction_samples": decision.telemetry.get("contradiction_samples"),
            "graph": decision.telemetry.get("graph"),
        }
        coverage_ratio = decision.telemetry.get("coverage_ratio")
        if isinstance(coverage_ratio, (int, float)):
            ratio_value = float(max(0.0, min(1.0, coverage_ratio)))
            event["coverage_ratio"] = ratio_value
            self.gate_coverage_ratios.append(ratio_value)
        agreement_meta = decision.telemetry.get("scout_agreement")
        if isinstance(agreement_meta, Mapping):
            stats = {str(key): value for key, value in agreement_meta.items()}
            score = stats.get("score")
            if not isinstance(score, (int, float)):
                fallback = stats.get("mean")
                if isinstance(fallback, (int, float)):
                    stats["score"] = float(fallback)
                else:
                    stats["score"] = 0.0
            else:
                stats["score"] = float(score)
            event["scout_agreement"] = dict(stats)
            self.gate_agreement_stats.append(dict(stats))
        outcome = decision.telemetry.get("decision_outcome")
        if isinstance(outcome, str) and outcome:
            normalized_outcome = outcome
        else:
            normalized_outcome = "debate" if decision.should_debate else "scout_exit"
        event["decision_outcome"] = normalized_outcome
        self.gate_decision_outcomes.append(normalized_outcome)
        graph_meta = event.get("graph")
        if isinstance(graph_meta, Mapping) and graph_meta:
            self.record_graph_build(graph_meta)
        self.gate_events.append(event)

    def record_graph_build(
        self,
        metadata: Mapping[str, Any] | None,
        *,
        summary: Mapping[str, Any] | None = None,
    ) -> None:
        """Capture telemetry about a knowledge graph ingestion run."""

        if not metadata or not isinstance(metadata, Mapping):
            return

        ingestion_meta = metadata.get("ingestion")
        entity_count = 0.0
        relation_count = 0.0
        ingestion_seconds = 0.0
        storage_latency: dict[str, float] = {}
        if isinstance(ingestion_meta, Mapping):
            entity_count = max(0.0, _safe_float(ingestion_meta.get("entity_count")))
            relation_count = max(0.0, _safe_float(ingestion_meta.get("relation_count")))
            ingestion_seconds = max(0.0, _safe_float(ingestion_meta.get("seconds")))
            storage_latency = _normalize_latency_mapping(
                ingestion_meta.get("storage_latency")
            )

        if entity_count <= 0.0 and relation_count <= 0.0 and not metadata.get("paths"):
            # Skip empty ingestions that did not add any graph structure.
            return

        GRAPH_BUILD_COUNTER.inc()
        if entity_count > 0.0:
            GRAPH_ENTITY_COUNTER.inc(entity_count)
        if relation_count > 0.0:
            GRAPH_RELATION_COUNTER.inc(relation_count)
        if ingestion_seconds > 0.0:
            GRAPH_BUILD_SECONDS.observe(ingestion_seconds)

        contradictions_meta = metadata.get("contradictions")
        contradiction_count = 0
        raw_contradiction_score = 0.0
        weighted_contradiction_score = 0.0
        contradiction_weight = 0.0
        contradiction_sample: list[dict[str, Any]] = []
        if isinstance(contradictions_meta, Mapping):
            items_raw = contradictions_meta.get("items")
            if isinstance(items_raw, Sequence):
                contradiction_count = len(items_raw)
                for item in items_raw:
                    if not isinstance(item, Mapping):
                        continue
                    subject = str(item.get("subject", ""))
                    predicate = str(item.get("predicate", ""))
                    objects_value = item.get("objects")
                    objects: list[str] = []
                    if isinstance(objects_value, Sequence):
                        for obj in objects_value:
                            objects.append(str(obj))
                    contradiction_sample.append(
                        {
                            "subject": subject,
                            "predicate": predicate,
                            "objects": objects,
                        }
                    )
                    if len(contradiction_sample) >= 5:
                        break
            raw_contradiction_score = max(
                0.0, _coerce_float(contradictions_meta.get("raw_score"))
            )
            weighted_contradiction_score = max(
                0.0, _coerce_float(contradictions_meta.get("weighted_score"))
            )
            contradiction_weight = max(
                0.0, _coerce_float(contradictions_meta.get("weight"))
            )
        if contradiction_count > 0:
            GRAPH_CONTRADICTION_COUNTER.inc(contradiction_count)

        neighbors_raw = metadata.get("neighbors")
        neighbor_node_count = 0
        neighbor_edge_count = 0
        neighbor_sample: dict[str, list[dict[str, str]]] = {}
        if isinstance(neighbors_raw, Mapping):
            for node, edges in neighbors_raw.items():
                if not isinstance(edges, Sequence):
                    continue
                neighbor_node_count += 1
                edge_list = list(edges)
                neighbor_edge_count += len(edge_list)
                if len(neighbor_sample) >= 3:
                    continue
                sanitized_edges: list[dict[str, str]] = []
                for edge in edge_list[:5]:
                    if not isinstance(edge, Mapping):
                        continue
                    sanitized_edges.append(
                        {
                            "target": str(edge.get("target", "")),
                            "predicate": str(edge.get("predicate", "")),
                            "direction": str(edge.get("direction", "")),
                        }
                    )
                if sanitized_edges:
                    neighbor_sample[str(node)] = sanitized_edges
        if neighbor_edge_count > 0:
            GRAPH_NEIGHBOR_COUNTER.inc(neighbor_edge_count)

        paths_raw = metadata.get("paths")
        path_count = 0
        path_sample: list[list[str]] = []
        if isinstance(paths_raw, Sequence):
            for path in paths_raw:
                if not isinstance(path, Sequence):
                    continue
                serialised = [str(node) for node in path]
                if not serialised:
                    continue
                path_count += 1
                if len(path_sample) < 3:
                    path_sample.append(serialised)

        similarity_meta = metadata.get("similarity")
        similarity_raw = 0.0
        similarity_weighted = 0.0
        similarity_weight = 0.0
        if isinstance(similarity_meta, Mapping):
            similarity_raw = max(0.0, _coerce_float(similarity_meta.get("raw_score")))
            similarity_weighted = max(
                0.0, _coerce_float(similarity_meta.get("weighted_score"))
            )
            similarity_weight = max(0.0, _coerce_float(similarity_meta.get("weight")))

        provenance_count = 0
        if summary and isinstance(summary, Mapping):
            provenance = summary.get("provenance")
            if isinstance(provenance, Sequence):
                provenance_count = len(provenance)

        record = {
            "timestamp": time.time(),
            "entity_count": entity_count,
            "relation_count": relation_count,
            "ingestion_seconds": ingestion_seconds,
            "storage_latency": storage_latency,
            "contradiction_count": float(contradiction_count),
            "contradiction_score": raw_contradiction_score,
            "contradiction_weighted": weighted_contradiction_score,
            "contradiction_weight": contradiction_weight,
            "contradiction_sample": contradiction_sample,
            "neighbor_node_count": float(neighbor_node_count),
            "neighbor_edge_count": float(neighbor_edge_count),
            "neighbor_sample": neighbor_sample,
            "path_count": float(path_count),
            "path_sample": path_sample,
            "similarity_score": similarity_raw,
            "similarity_weighted": similarity_weighted,
            "similarity_weight": similarity_weight,
            "provenance_count": float(provenance_count),
        }

        self.graph_ingestions.append(record)
        if len(self.graph_ingestions) > self._max_sample_history:
            del self.graph_ingestions[0 : len(self.graph_ingestions) - self._max_sample_history]

        log.info(
            "Recorded graph ingestion metrics",
            extra={
                "graph_entities": entity_count,
                "graph_relations": relation_count,
                "graph_contradictions": contradiction_count,
                "graph_neighbors": neighbor_edge_count,
                "graph_ingestion_seconds": ingestion_seconds,
            },
        )

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

        graph_summary_payload: dict[str, Any] | None = None
        if self.graph_ingestions:
            runs = len(self.graph_ingestions)
            totals = _empty_graph_totals()
            storage_totals: dict[str, float] = {}
            for record in self.graph_ingestions:
                _accumulate_graph_totals(totals, record)
                latency_meta = record.get("storage_latency")
                if isinstance(latency_meta, Mapping):
                    for key, value in latency_meta.items():
                        name = str(key)
                        storage_totals[name] = storage_totals.get(name, 0.0) + _safe_float(
                            value
                        )
            averages: dict[str, float | dict[str, float]] = {
                key: (totals[key] / runs if runs else 0.0) for key in totals
            }
            averages["storage_latency"] = {
                key: value / runs if runs else 0.0 for key, value in storage_totals.items()
            }
            latest_source = self.graph_ingestions[-1]
            latest_raw: dict[str, Any] = {}
            for key, value in latest_source.items():
                if key in totals:
                    latest_raw[key] = _safe_float(value)
                    continue
                if key == "storage_latency" and isinstance(value, Mapping):
                    latest_raw[key] = {str(name): _safe_float(v) for name, v in value.items()}
                    continue
                if key == "contradiction_sample" and isinstance(value, Sequence):
                    latest_raw[key] = [
                        dict(item) for item in value if isinstance(item, Mapping)
                    ]
                    continue
                if key == "neighbor_sample" and isinstance(value, Mapping):
                    latest_raw[key] = {
                        str(node): [
                            dict(edge)
                            for edge in edges
                            if isinstance(edge, Mapping)
                        ]
                        for node, edges in value.items()
                        if isinstance(edges, Sequence)
                    }
                    continue
                if key == "path_sample" and isinstance(value, Sequence):
                    latest_raw[key] = [
                        [str(node) for node in path]
                        for path in value
                        if isinstance(path, Sequence)
                    ]
                    continue
                latest_raw[key] = value

            graph_summary_payload = {
                "runs": runs,
                "totals": totals,
                "totals_storage_latency": dict(storage_totals),
                "averages": averages,
                "latest": latest_raw,
            }

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
            "model_routing_overrides": [
                override.to_dict() for override in self.routing_override_requests
            ],
            "model_routing_strategy": self.routing_strategy,
            "model_routing_agent_constraints": {
                agent: dict(constraints)
                for agent, constraints in self.routing_agent_constraints.items()
            },
            "model_routing_recommendations": dict(self.routing_agent_recommendations),
            "graph_ingestion": graph_summary_payload or {},
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

    def apply_model_routing(
        self,
        agent_name: str,
        config: "ConfigModel",
        state: "QueryState | None" = None,
    ) -> str | None:
        """Return a budget-aware model recommendation without mutating ``config``."""

        routing_cfg = getattr(config, "model_routing", None)
        if (
            routing_cfg is None
            or not routing_cfg.enabled
            or not routing_cfg.model_profiles
        ):
            return None

        self.routing_strategy = routing_cfg.strategy_name

        if state is not None:
            overrides_payload = state.metadata.get("routing_overrides")
            state_overrides = ingest_state_overrides(overrides_payload)
            if state_overrides:
                state.metadata["routing_overrides"] = []
                for override in state_overrides:
                    self._register_override(override)

        agent_cfg = config.agent_config.get(agent_name)
        directives = resolve_agent_directives(
            agent_name,
            config,
            routing_cfg,
            agent_cfg,
            self.routing_override_requests,
        )

        token_share = directives.token_share
        if token_share is None:
            token_share = self._default_token_share(config, agent_name)
        agent_budget_tokens = directives.budget_tokens
        if agent_budget_tokens is None and config.token_budget is not None:
            agent_budget_tokens = max(config.token_budget * token_share, 0.0)

        latency_slo = directives.latency_slo_ms
        allowed = directives.allowed_models
        preferred = directives.preferred_models
        if allowed is not None and not allowed:
            allowed = None
        if preferred is not None and not preferred:
            preferred = None
        current_model = (
            agent_cfg.model
            if agent_cfg and agent_cfg.model
            else directives.default_model or config.default_model
        )

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

        metadata: dict[str, Any] = {
            "policy": directives.policy_name,
            "strategy": directives.strategy_name,
            "token_share": token_share,
            "budget_tokens": agent_budget_tokens,
            "latency_slo_ms": latency_slo,
            "latency_cap_ms": decision.latency_cap_ms,
            "applied": False,
        }
        if directives.override is not None:
            metadata["override"] = directives.override.to_dict()
        decision = replace(decision, metadata=metadata)
        self.routing_decisions.append(decision)

        constraints: dict[str, float | None] = {
            "token_share": token_share,
            "budget_tokens": agent_budget_tokens,
            "latency_slo_ms": latency_slo,
            "latency_cap_ms": decision.latency_cap_ms,
        }
        self.routing_agent_constraints[agent_name] = constraints
        self.routing_agent_recommendations[agent_name] = decision.selected_model

        log_payload = decision.as_log_extra()
        log_payload["applied"] = False
        log.info("Evaluated budget-aware model routing", extra=log_payload)

        selected = decision.selected_model
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

    def persist_model_routing_metrics(self, path: Path | None = None) -> None:
        """Append routing telemetry to ``path`` for dashboard ingestion."""

        summary = self.get_summary()
        record = {
            "timestamp": time.time(),
            "strategy": summary.get("model_routing_strategy"),
            "decisions": summary.get("model_routing_decisions", []),
            "overrides": summary.get("model_routing_overrides", []),
            "agent_latency_p95_ms": summary.get("agent_latency_p95_ms", {}),
            "agent_avg_tokens": summary.get("agent_avg_tokens", {}),
            "agent_constraints": summary.get("model_routing_agent_constraints", {}),
            "agent_recommendations": summary.get(
                "model_routing_recommendations", {}
            ),
        }
        if path is None:
            path = Path(
                getenv(
                    "AUTORESEARCH_ROUTING_METRICS",
                    "tests/integration/baselines/model_routing.json",
                )
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

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
