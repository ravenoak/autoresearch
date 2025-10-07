"""
Orchestration system coordinating multi-agent dialectical cycles.

Provides direct, dialectical, and chain-of-thought reasoning modes with
state management, metrics, token tracking, and parallel execution. Behavior
is exercised by unit and integration tests under ``tests/``.
"""

from __future__ import annotations

import asyncio
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, Sequence, cast

import rdflib

from ..agents.registry import AgentFactory, AgentRegistry
from ..config.models import ConfigModel
from ..errors import (  # noqa: F401
    AgentError,
    NotFoundError,
    OrchestrationError,
    TimeoutError,
)
from ..logging_utils import get_logger
from ..models import QueryResponse
from ..storage import StorageManager
from ..tracing import get_tracer, setup_tracing
from .circuit_breaker import CircuitBreakerManager, CircuitBreakerState
from .metrics import OrchestrationMetrics, record_query
from .orchestration_utils import OrchestrationUtils, ScoutGateDecision
from .reasoning import ChainOfThoughtStrategy, ReasoningMode
from .reasoning_payloads import FrozenReasoningStep, normalize_reasoning_step
from .state import QueryState
from .state_registry import QueryStateRegistry
from .token_utils import _capture_token_usage
from .types import CallbackMap, CycleCallback, TracerProtocol

log = get_logger(__name__)


def _freeze_payload(value: Any) -> Any:
    """Return ``value`` with mappings and sequences converted into immutable views."""

    if isinstance(value, FrozenReasoningStep):
        return value
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_payload(val) for key, val in value.items()})
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(_freeze_payload(item) for item in value)
    return value


def _freeze_warning_entries(
    warnings: Sequence[Any] | None,
) -> tuple[Mapping[str, Any], ...]:
    """Normalise warning telemetry into immutable mapping snapshots."""

    if not warnings:
        return ()

    frozen_warnings: list[Mapping[str, Any]] = []
    for warning in warnings:
        if isinstance(warning, Mapping):
            frozen_entry = cast(Mapping[str, Any], _freeze_payload(warning))
            frozen_warnings.append(frozen_entry)
    return tuple(frozen_warnings)


def _strip_warning_banners(answer: str) -> str:
    """Remove trailing warning banners prefixed with the caution glyph."""

    if not answer:
        return answer

    lines = answer.splitlines()
    trimmed = list(lines)

    while trimmed:
        candidate = trimmed[-1]
        if not candidate.strip():
            trimmed.pop()
            continue
        if candidate.lstrip().startswith("⚠️"):
            trimmed.pop()
            continue
        break

    return "\n".join(trimmed).rstrip()


def _snapshot_scout_sample(sample_state: "QueryState", sample_index: int) -> Mapping[str, Any]:
    """Return an immutable snapshot of a scout sample for telemetry.

    Args:
        sample_state: Query state produced by the scout synthesiser run.
        sample_index: Zero-based index identifying the sample order.

    Returns:
        Mapping providing the scout answer and frozen claim payloads.
    """

    normalized_claims: list[FrozenReasoningStep] = []
    for claim in sample_state.claims:
        normalized = normalize_reasoning_step(claim)
        if len(normalized):
            normalized_claims.append(normalized)

    warnings_snapshot = _freeze_warning_entries(
        cast(
            Sequence[Any] | None,
            sample_state.metadata.get("warnings") if isinstance(sample_state.metadata, Mapping) else None,
        )
    )

    answer_value = sample_state.results.get("final_answer")
    answer_snapshot: str | Mapping[str, Any] | tuple[Any, ...] | None
    if isinstance(answer_value, str):
        answer_snapshot = _strip_warning_banners(answer_value)
    elif answer_value is None:
        answer_snapshot = None
    elif isinstance(answer_value, Mapping):
        answer_snapshot = cast(Mapping[str, Any], _freeze_payload(answer_value))
    elif isinstance(answer_value, Sequence) and not isinstance(
        answer_value,
        (str, bytes, bytearray),
    ):
        answer_snapshot = cast(tuple[Any, ...], _freeze_payload(answer_value))
    else:
        answer_snapshot = str(answer_value)

    payload: dict[str, Any] = {
        "index": sample_index,
        "answer": answer_snapshot,
        "claims": tuple(normalized_claims),
    }
    if warnings_snapshot:
        payload["warnings"] = warnings_snapshot

    return MappingProxyType(payload)


def _reduce_auto_mode_metadata(
    existing: Mapping[str, Any] | None,
    decision: "ScoutGateDecision",
    *,
    final_answer: Any,
    scout_samples: tuple[Mapping[str, Any], ...],
) -> dict[str, Any]:
    """Normalise AUTO mode metadata with scout samples and gate telemetry.

    Args:
        existing: Prior AUTO mode metadata to merge into the snapshot.
        decision: Gate decision emitted after scout evaluation.
        final_answer: Final answer from the scout synthesiser run.
        scout_samples: Tuple of frozen scout sample payloads.

    Returns:
        Fresh metadata dictionary safe for downstream mutation.
    """

    metadata: dict[str, Any] = {}
    if isinstance(existing, Mapping):
        metadata.update({str(key): value for key, value in existing.items()})

    metadata.update(
        {
            "scout_answer": final_answer,
            "scout_should_debate": decision.should_debate,
            "scout_reason": decision.reason,
            "scout_samples": scout_samples,
            "scout_sample_count": len(scout_samples),
        }
    )

    scout_agreement = decision.heuristics.get("scout_agreement")
    metadata["scout_agreement"] = scout_agreement

    return metadata


class Orchestrator:
    """Coordinates multi-agent dialectical cycles with rotating Primus."""

    # Expose token usage capture helper for tests that monkeypatch the
    # orchestrator directly. Previously this utility lived only within
    # ``token_utils``, which caused AttributeError in tests expecting
    # ``Orchestrator._capture_token_usage``.
    _capture_token_usage = staticmethod(_capture_token_usage)

    def __init__(self) -> None:
        """Initialize orchestrator state for a single query."""
        self._cb_manager: CircuitBreakerManager | None = None

    @staticmethod
    def _parse_config(config: ConfigModel) -> Dict[str, Any]:
        """Parse configuration and extract relevant parameters."""
        agents = getattr(
            config,
            "agents",
            ["Synthesizer", "Contrarian", "FactChecker"],
        )
        primus_index = getattr(config, "primus_start", 0)
        loops = getattr(config, "loops", 2)
        mode = getattr(config, "reasoning_mode", ReasoningMode.DIALECTICAL)
        max_errors = getattr(config, "max_errors", 3)
        cb_threshold = getattr(config, "circuit_breaker_threshold", 3)
        cb_cooldown = getattr(config, "circuit_breaker_cooldown", 30)
        retry_attempts = getattr(config, "retry_attempts", 1)
        retry_backoff = getattr(config, "retry_backoff", 0.0)
        enable_messages = getattr(config, "enable_agent_messages", False)
        coalitions = getattr(config, "coalitions", {})
        for cname, members in coalitions.items():
            if AgentRegistry.get_coalition_obj(cname) is None:
                AgentRegistry.create_coalition(cname, members)
        enable_feedback = getattr(config, "enable_feedback", False)

        if mode == ReasoningMode.DIRECT:
            agents = ["Synthesizer"]
            loops = 1
            agent_groups: List[List[str]] = [["Synthesizer"]]
        else:
            agent_groups = [
                coalition.members if (coalition := AgentRegistry.get_coalition_obj(a)) else [a]
                for a in agents
            ]

        return {
            "agents": agents,
            "agent_groups": agent_groups,
            "primus_index": primus_index,
            "loops": loops,
            "mode": mode,
            "max_errors": max_errors,
            "circuit_breaker_threshold": cb_threshold,
            "circuit_breaker_cooldown": cb_cooldown,
            "retry_attempts": retry_attempts,
            "retry_backoff": retry_backoff,
            "enable_agent_messages": enable_messages,
            "enable_feedback": enable_feedback,
            "coalitions": coalitions,
        }

    def get_circuit_breaker_state(self, agent_name: str) -> CircuitBreakerState:
        if self._cb_manager is None:
            return {
                "state": "closed",
                "failure_count": 0.0,
                "last_failure_time": 0.0,
                "recovery_attempts": 0,
            }
        return self._cb_manager.get_circuit_breaker_state(agent_name)

    def run_query(
        self,
        query: str,
        config: ConfigModel,
        callbacks: CallbackMap | None = None,
        *,
        agent_factory: type[AgentFactory] = AgentFactory,
        storage_manager: type[StorageManager] = StorageManager,
        visualize: bool = False,
    ) -> QueryResponse:
        """Run a query through dialectical agent cycles."""
        setup_tracing(getattr(config, "tracing_enabled", False))
        tracer_protocol = cast(TracerProtocol, get_tracer(__name__))
        record_query()
        metrics = OrchestrationMetrics()
        callbacks_map: CallbackMap = cast(CallbackMap, callbacks or {})

        if visualize:
            log.debug("Visualization requested for query")

        config_params = self._parse_config(config)
        agents = config_params["agent_groups"]
        primus_index = config_params["primus_index"]
        loops = config_params["loops"]
        mode = config_params["mode"]
        max_errors = config_params["max_errors"]
        cb_manager = CircuitBreakerManager(
            config_params["circuit_breaker_threshold"],
            config_params["circuit_breaker_cooldown"],
        )
        self._cb_manager = cb_manager

        OrchestrationUtils.apply_adaptive_token_budget(config, query)

        token_budget = getattr(config, "token_budget", None)
        if (
            token_budget is not None
            and hasattr(config, "group_size")
            and hasattr(config, "total_groups")
        ):
            total_agents = getattr(
                config,
                "total_agents",
                config.group_size * config.total_groups,
            )
            if total_agents:
                group_tokens = max(1, token_budget * config.group_size // total_agents)
                config.token_budget = group_tokens

        original_mode_setting = getattr(config, "reasoning_mode", ReasoningMode.DIALECTICAL)

        if mode == ReasoningMode.CHAIN_OF_THOUGHT:
            strategy = ChainOfThoughtStrategy()
            return strategy.run_query(
                query,
                config,
                agent_factory=agent_factory,
            )

        state = QueryState(
            query=query,
            primus_index=primus_index,
            coalitions=config_params.get("coalitions", {}),
        )

        decision: ScoutGateDecision | None = None

        scout_samples: list[Mapping[str, Any]] = []

        if mode == ReasoningMode.AUTO:
            scout_state = state
            metrics.start_cycle()
            cycle_start = cast(CycleCallback | None, callbacks_map.get("on_cycle_start"))
            if cycle_start is not None:
                cycle_start(0, scout_state)
            try:
                config.reasoning_mode = ReasoningMode.DIRECT
                OrchestrationUtils.execute_agent(
                    "Synthesizer",
                    scout_state,
                    config,
                    metrics,
                    callbacks_map,
                    agent_factory,
                    storage_manager,
                    0,
                    cb_manager,
                )
            finally:
                config.reasoning_mode = original_mode_setting
            metrics.end_cycle()
            cycle_end = cast(CycleCallback | None, callbacks_map.get("on_cycle_end"))
            if cycle_end is not None:
                cycle_end(0, scout_state)
            scout_state.metadata["execution_metrics"] = metrics.get_summary()
            metrics.record_query_tokens(query)

            scout_samples.append(_snapshot_scout_sample(scout_state, 0))

            extra_samples = max(0, int(getattr(config, "auto_scout_samples", 0)))
            if extra_samples:
                for sample_index in range(1, extra_samples + 1):
                    sample_state = QueryState(
                        query=query,
                        primus_index=primus_index,
                        coalitions=config_params.get("coalitions", {}),
                    )
                    try:
                        config.reasoning_mode = ReasoningMode.DIRECT
                        OrchestrationUtils.execute_agent(
                            "Synthesizer",
                            sample_state,
                            config,
                            metrics,
                            callbacks_map,
                            agent_factory,
                            storage_manager,
                            0,
                            cb_manager,
                        )
                    finally:
                        config.reasoning_mode = original_mode_setting
                    scout_samples.append(_snapshot_scout_sample(sample_state, sample_index))

            scout_samples_view = tuple(scout_samples)
            scout_state.metadata["scout_samples"] = scout_samples_view

            decision = OrchestrationUtils.evaluate_scout_gate_policy(
                query=query,
                config=config,
                state=scout_state,
                loops=loops,
                metrics=metrics,
            )

            auto_meta = _reduce_auto_mode_metadata(
                cast(Mapping[str, Any] | None, scout_state.metadata.get("auto_mode")),
                decision,
                final_answer=scout_state.results.get("final_answer"),
                scout_samples=scout_samples_view,
            )
            scout_state.metadata["auto_mode"] = auto_meta

            scout_answer_value = auto_meta.get("scout_answer")
            if isinstance(scout_answer_value, str):
                sanitized_scout_answer = _strip_warning_banners(scout_answer_value)
                if sanitized_scout_answer != scout_answer_value:
                    auto_meta["scout_answer"] = sanitized_scout_answer
                scout_state.results["final_answer"] = sanitized_scout_answer

            if not decision.should_debate:
                auto_meta["outcome"] = "direct_exit"
                config.reasoning_mode = original_mode_setting
                response = scout_state.synthesize()

                raw_answer = cast(str, scout_state.results.get("final_answer", response.answer))
                sanitized_answer = _strip_warning_banners(raw_answer)
                response.answer = sanitized_answer
                scout_state.results["final_answer"] = sanitized_answer
                auto_meta["scout_answer"] = sanitized_answer

                warning_entries = _freeze_warning_entries(response.warnings)
                scout_state.metadata["warnings"] = warning_entries
                if warning_entries:
                    auto_meta["warnings"] = warning_entries
                else:
                    auto_meta.pop("warnings", None)

                existing_samples = tuple(
                    cast(
                        Sequence[Mapping[str, Any]],
                        scout_state.metadata.get("scout_samples", ()),
                    )
                )
                refreshed_samples: tuple[Mapping[str, Any], ...]
                if existing_samples:
                    tail = existing_samples[1:]
                    refreshed_samples = (_snapshot_scout_sample(scout_state, 0), *tail)
                else:
                    refreshed_samples = (_snapshot_scout_sample(scout_state, 0),)

                scout_state.metadata["scout_samples"] = refreshed_samples
                auto_meta["scout_samples"] = refreshed_samples
                auto_meta["scout_sample_count"] = len(refreshed_samples)

                response.metrics["auto_mode"] = auto_meta
                response.metrics["scout_samples"] = refreshed_samples

                return response

            auto_meta["outcome"] = "escalated"
            auto_meta["escalation_mode"] = ReasoningMode.DIALECTICAL.value
            gate_snapshot = scout_state.metadata.get("scout_gate")
            preserved_metadata = {
                key: value
                for key, value in scout_state.metadata.items()
                if key.startswith("scout_")
            }
            state = QueryState(
                query=query,
                primus_index=primus_index,
                coalitions=config_params.get("coalitions", {}),
            )
            preserved_claims = [
                normalize_reasoning_step(claim)
                for claim in scout_state.claims
                if len(claim)
            ]
            if preserved_claims:
                state.claims.extend(preserved_claims)
            preserved_warnings = _freeze_warning_entries(
                cast(
                    Sequence[Any] | None,
                    scout_state.metadata.get("warnings")
                    if isinstance(scout_state.metadata, Mapping)
                    else None,
                )
            )
            if not preserved_warnings and scout_samples_view:
                sample_warnings = scout_samples_view[0].get("warnings")
                if isinstance(sample_warnings, tuple):
                    preserved_warnings = cast(tuple[Mapping[str, Any], ...], sample_warnings)
            if preserved_warnings:
                state.metadata["warnings"] = preserved_warnings
            if gate_snapshot is not None:
                state.metadata["scout_gate"] = gate_snapshot
            for key, value in preserved_metadata.items():
                state.metadata.setdefault(key, value)
            state.metadata["auto_mode"] = dict(auto_meta)
            config.reasoning_mode = ReasoningMode.DIALECTICAL
            mode = ReasoningMode.DIALECTICAL

        if decision is None:
            decision = OrchestrationUtils.evaluate_scout_gate_policy(
                query=query,
                config=config,
                state=state,
                loops=loops,
                metrics=metrics,
            )
        if decision.target_loops != loops:
            log.info(
                "Scout gate reduced debate loops",
                extra={
                    "original_loops": loops,
                    "target_loops": decision.target_loops,
                    "reason": decision.reason,
                    "heuristics": decision.heuristics,
                    "thresholds": decision.thresholds,
                    "tokens_saved_estimate": decision.tokens_saved,
                },
            )
        else:
            log.debug(
                "Scout gate proceeding with configured loops",
                extra={
                    "loops": loops,
                    "reason": decision.reason,
                    "heuristics": decision.heuristics,
                    "thresholds": decision.thresholds,
                },
            )
        loops = decision.target_loops

        try:
            total_agents = sum(len(g) for g in agents)
            log.info(
                f"Starting dialectical process with {total_agents} agents in {len(agents)} groups and {loops} loops",
                extra={
                    "agents": agents,
                    "loops": loops,
                    "primus_index": primus_index,
                    "max_errors": max_errors,
                    "reasoning_mode": str(mode),
                },
            )

            for loop in range(loops):
                log.debug(
                    f"Starting loop {loop + 1}/{loops} with primus_index {primus_index}",
                    extra={
                        "loop": loop + 1,
                        "total_loops": loops,
                        "primus_index": primus_index,
                    },
                )

                primus_index = OrchestrationUtils.execute_cycle(
                    loop,
                    loops,
                    agents,
                    primus_index,
                    max_errors,
                    state,
                    config,
                    metrics,
                    callbacks_map,
                    agent_factory,
                    storage_manager,
                    tracer_protocol,
                    cb_manager,
                )

                if "error" in state.results:
                    log.error(
                        f"Aborting dialectical process due to error: {state.results['error']}",
                        extra={
                            "error": state.results["error"],
                            "error_count": state.error_count,
                        },
                    )
                    break

                log.debug(
                    f"Completed loop {loop + 1}/{loops}, new primus_index: {primus_index}",
                    extra={
                        "loop": loop + 1,
                        "total_loops": loops,
                        "primus_index": primus_index,
                        "cycle": state.cycle,
                        "error_count": state.error_count,
                    },
                )

            state.metadata["execution_metrics"] = metrics.get_summary()
            metrics.record_query_tokens(query)

            if "error" in state.results or state.error_count > 0:
                error_message = state.results.get(
                    "error", f"Process completed with {state.error_count} errors"
                )
                raise OrchestrationError(
                    error_message,
                    cause=None,
                    errors=state.metadata.get("errors", []),
                    suggestion="Check the agent execution logs for details on the specific error and ensure all agents are properly configured",
                )

            response = state.synthesize()
            state_id = QueryStateRegistry.register(state, config)
            response.state_id = state_id
            return response
        finally:
            config.reasoning_mode = original_mode_setting

    async def run_query_async(
        self,
        query: str,
        config: ConfigModel,
        callbacks: CallbackMap | None = None,
        *,
        agent_factory: type[AgentFactory] = AgentFactory,
        storage_manager: type[StorageManager] = StorageManager,
        concurrent: bool = False,
    ) -> QueryResponse:
        """Asynchronous wrapper around :meth:`run_query`."""
        setup_tracing(getattr(config, "tracing_enabled", False))
        tracer_protocol = cast(TracerProtocol, get_tracer(__name__))
        record_query()
        metrics = OrchestrationMetrics()
        callbacks_map: CallbackMap = cast(CallbackMap, callbacks or {})

        config_params = self._parse_config(config)
        agents = config_params["agent_groups"]
        primus_index = config_params["primus_index"]
        loops = config_params["loops"]
        mode = config_params["mode"]
        max_errors = config_params["max_errors"]
        cb_manager = CircuitBreakerManager(
            config_params["circuit_breaker_threshold"],
            config_params["circuit_breaker_cooldown"],
        )
        self._cb_manager = cb_manager

        OrchestrationUtils.apply_adaptive_token_budget(config, query)

        token_budget = getattr(config, "token_budget", None)
        if (
            token_budget is not None
            and hasattr(config, "group_size")
            and hasattr(config, "total_groups")
        ):
            total_agents = getattr(
                config,
                "total_agents",
                config.group_size * config.total_groups,
            )
            if total_agents:
                group_tokens = max(1, token_budget * config.group_size // total_agents)
                config.token_budget = group_tokens

        if mode == ReasoningMode.CHAIN_OF_THOUGHT:
            strategy = ChainOfThoughtStrategy()
            return await asyncio.to_thread(
                strategy.run_query,
                query,
                config,
                agent_factory=agent_factory,
            )

        state = QueryState(
            query=query,
            primus_index=primus_index,
            coalitions=config_params.get("coalitions", {}),
        )

        decision = OrchestrationUtils.evaluate_scout_gate_policy(
            query=query,
            config=config,
            state=state,
            loops=loops,
            metrics=metrics,
        )
        if decision.target_loops != loops:
            log.info(
                "Scout gate reduced debate loops",
                extra={
                    "original_loops": loops,
                    "target_loops": decision.target_loops,
                    "reason": decision.reason,
                    "heuristics": decision.heuristics,
                    "thresholds": decision.thresholds,
                    "tokens_saved_estimate": decision.tokens_saved,
                },
            )
        else:
            log.debug(
                "Scout gate proceeding with configured loops",
                extra={
                    "loops": loops,
                    "reason": decision.reason,
                    "heuristics": decision.heuristics,
                    "thresholds": decision.thresholds,
                },
            )
        loops = decision.target_loops

        total_agents = sum(len(g) for g in agents)
        log.info(
            f"Starting dialectical process with {total_agents} agents in {len(agents)} groups and {loops} loops",
            extra={
                "agents": agents,
                "loops": loops,
                "primus_index": primus_index,
                "max_errors": max_errors,
                "reasoning_mode": str(mode),
            },
        )

        for loop in range(loops):
            log.debug(
                f"Starting loop {loop + 1}/{loops} with primus_index {primus_index}",
                extra={
                    "loop": loop + 1,
                    "total_loops": loops,
                    "primus_index": primus_index,
                },
            )

            primus_index = await OrchestrationUtils.execute_cycle_async(
                loop,
                loops,
                agents,
                primus_index,
                max_errors,
                state,
                config,
                metrics,
                callbacks_map,
                agent_factory,
                storage_manager,
                tracer_protocol,
                concurrent=concurrent,
                cb_manager=cb_manager,
            )

            if "error" in state.results:
                log.error(
                    f"Aborting dialectical process due to error: {state.results['error']}",
                    extra={
                        "error": state.results["error"],
                        "error_count": state.error_count,
                    },
                )
                break

            log.debug(
                f"Completed loop {loop + 1}/{loops}, new primus_index: {primus_index}",
                extra={
                    "loop": loop + 1,
                    "total_loops": loops,
                    "primus_index": primus_index,
                    "cycle": state.cycle,
                    "error_count": state.error_count,
                },
            )

        state.metadata["execution_metrics"] = metrics.get_summary()
        metrics.record_query_tokens(query)

        if "error" in state.results or state.error_count > 0:
            error_message = state.results.get(
                "error", f"Process completed with {state.error_count} errors"
            )
            raise OrchestrationError(
                error_message,
                cause=None,
                errors=state.metadata.get("errors", []),
                suggestion="Check the agent execution logs for details on the specific error and ensure all agents are properly configured",
            )

        return state.synthesize()

    @staticmethod
    def run_parallel_query(
        query: str,
        config: ConfigModel,
        agent_groups: Sequence[Sequence[str]],
        timeout: int = 300,
    ) -> QueryResponse:
        """Run multiple parallel agent groups and synthesize results."""
        from . import parallel

        normalized_groups = [list(group) for group in agent_groups]
        return parallel.execute_parallel_query(query, config, normalized_groups, timeout)

    @staticmethod
    def infer_relations() -> None:
        """Infer ontology relations via the storage manager."""
        StorageManager.infer_relations()

    @staticmethod
    def query_ontology(query: str) -> rdflib.query.Result:
        """Query the ontology graph via the storage manager."""
        return StorageManager.query_ontology(query)
