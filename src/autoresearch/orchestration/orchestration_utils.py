"""Utility helpers for orchestration components.

This module groups functions that were previously attached dynamically to
:class:`~autoresearch.orchestration.orchestrator.Orchestrator`. Keeping them in a
separate utility class makes the helpers easier to import directly in tests and
other modules without relying on dynamic attribute assignment.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean
from typing import Iterable, Sequence

from ..config.models import ConfigModel
from ..search.context import SearchContext
from .budgeting import _apply_adaptive_token_budget
from .error_handling import (
    _apply_recovery_strategy,
    _categorize_error,
    _handle_agent_error,
)
from .execution import (
    _call_agent_start_callback,
    _check_agent_can_execute,
    _deliver_messages,
    _execute_agent,
    _execute_agent_with_token_counting,
    _execute_cycle,
    _execute_cycle_async,
    _get_agent,
    _handle_agent_completion,
    _log_agent_execution,
    _log_sources,
    _persist_claims,
    _rotate_list,
)
from .metrics import OrchestrationMetrics
from .state import QueryState
from .token_utils import _capture_token_usage, _execute_with_adapter
from .utils import calculate_result_confidence, get_memory_usage


@dataclass
class ScoutGateDecision:
    """Decision emitted by :class:`ScoutGatePolicy`."""

    should_debate: bool
    target_loops: int
    heuristics: dict[str, float]
    thresholds: dict[str, float]
    reason: str
    tokens_saved: int


class ScoutGatePolicy:
    """Compute scout-stage heuristics to decide on debate depth."""

    def __init__(self, config: ConfigModel):
        self.config = config

    def evaluate(
        self,
        *,
        query: str,
        state: QueryState,
        loops: int,
        metrics: OrchestrationMetrics,
    ) -> ScoutGateDecision:
        """Return a :class:`ScoutGateDecision` for ``state`` and ``query``."""

        thresholds = {
            "retrieval_overlap": getattr(self.config, "gate_retrieval_overlap_threshold", 0.6),
            "nli_conflict": getattr(self.config, "gate_nli_conflict_threshold", 0.3),
            "complexity": getattr(self.config, "gate_complexity_threshold", 0.5),
        }

        heuristics = {
            "retrieval_overlap": self._retrieval_overlap(state),
            "nli_conflict": self._nli_conflict(state),
            "complexity": self._complexity(query, state),
        }

        overrides = getattr(self.config, "gate_user_overrides", {})
        signal_overrides = overrides.get("signals", {}) if isinstance(overrides, dict) else {}
        for key, value in signal_overrides.items():
            if key in heuristics:
                try:
                    heuristics[key] = float(value)
                except (TypeError, ValueError):
                    continue

        enabled = getattr(self.config, "gate_policy_enabled", True)
        decision_override = None
        if isinstance(overrides, dict):
            decision_override = overrides.get("decision") or overrides.get("mode")
        reason = "policy_enabled" if enabled else "policy_disabled"

        if decision_override:
            normalized = str(decision_override).lower()
            if normalized in {"force_debate", "debate", "full"}:
                should_debate = True
                reason = "override_force_debate"
            elif normalized in {"force_exit", "exit", "scout_only"}:
                should_debate = False
                reason = "override_force_exit"
            else:
                should_debate = enabled and self._auto_decide(heuristics, thresholds)
                reason = f"override_unknown:{normalized}"
        else:
            should_debate = enabled and self._auto_decide(heuristics, thresholds)
        target_loops = loops if should_debate else min(loops, 1)

        tokens_saved = self._estimate_tokens_saved(loops, target_loops)

        decision = ScoutGateDecision(
            should_debate=should_debate,
            target_loops=target_loops,
            heuristics=heuristics,
            thresholds=thresholds,
            reason=reason,
            tokens_saved=tokens_saved,
        )
        metrics.record_gate_decision(decision)
        state.metadata.setdefault("scout_gate", asdict(decision))
        return decision

    def _auto_decide(
        self, heuristics: dict[str, float], thresholds: dict[str, float]
    ) -> bool:
        """Return ``True`` when multi-loop debate should proceed."""

        # Debate when evidence coverage looks insufficient or uncertainty is high.
        overlap_low = heuristics["retrieval_overlap"] < thresholds["retrieval_overlap"]
        conflict_high = heuristics["nli_conflict"] >= thresholds["nli_conflict"]
        complexity_high = heuristics["complexity"] >= thresholds["complexity"]
        return overlap_low or conflict_high or complexity_high

    def _estimate_tokens_saved(self, loops: int, target_loops: int) -> int:
        """Estimate tokens saved when reducing debate loops."""

        if loops <= target_loops:
            return 0
        budget = getattr(self.config, "token_budget", None)
        if not budget:
            return 0
        per_loop = max(1, budget // max(1, loops))
        return (loops - target_loops) * per_loop

    def _retrieval_overlap(self, state: QueryState) -> float:
        """Return overlap metric from scout retrieval artifacts."""

        retrieval_sets = state.metadata.get("scout_retrieval_sets")
        if isinstance(retrieval_sets, Sequence) and len(retrieval_sets) > 1:
            pairwise_scores: list[float] = []
            normalized = [self._normalize_iterable(s) for s in retrieval_sets]
            for idx, current in enumerate(normalized):
                for other in normalized[idx + 1 :]:
                    union = current | other
                    if not union:
                        pairwise_scores.append(1.0)
                    else:
                        pairwise_scores.append(len(current & other) / len(union))
            if pairwise_scores:
                return float(sum(pairwise_scores) / len(pairwise_scores))
        if state.sources:
            seen = {self._extract_source_id(s) for s in state.sources}
            unique = len(seen)
            return 1.0 - (unique / max(len(state.sources), 1))
        return 0.0

    def _nli_conflict(self, state: QueryState) -> float:
        """Aggregate contradiction probabilities from scout entailment checks."""

        scores = state.metadata.get("scout_entailment_scores")
        values: list[float] = []
        if isinstance(scores, Sequence):
            for item in scores:
                if isinstance(item, dict):
                    for key in ("contradiction", "conflict", "score"):
                        value = item.get(key)
                        if value is not None:
                            try:
                                values.append(float(value))
                            except (TypeError, ValueError):
                                continue
                            break
                else:
                    try:
                        values.append(float(item))
                    except (TypeError, ValueError):
                        continue
        try:
            graph_signal = SearchContext.get_instance().get_contradiction_signal()
        except Exception:
            graph_signal = 0.0
        if graph_signal:
            values.append(float(graph_signal))
        if values:
            return float(mean(values))
        return 0.0

    def _complexity(self, query: str, state: QueryState) -> float:
        """Estimate question complexity using scout features and query length."""

        features = state.metadata.get("scout_complexity_features")
        hop_score = 0.0
        entity_score = 0.0
        other_score = 0.0
        if isinstance(features, dict):
            hops = max(0, float(features.get("hops", 0)))
            hop_score = min(1.0, hops / 3.0)
            entities = features.get("entities")
            if isinstance(entities, Sequence) and not isinstance(entities, (str, bytes)):
                entity_count = len(entities)
            else:
                try:
                    entity_count = int(features.get("entity_count", 0))
                except (TypeError, ValueError):
                    entity_count = 0
            entity_score = min(1.0, entity_count / 10.0)
            clauses = features.get("clauses")
            try:
                clause_score = float(clauses) / 5.0
            except (TypeError, ValueError):
                clause_score = 0.0
            other_score = max(0.0, min(clause_score, 1.0))
        query_tokens = len(query.split())
        length_score = min(1.0, query_tokens / 200.0)
        combined = 0.4 * hop_score + 0.3 * entity_score + 0.2 * other_score + 0.1 * length_score
        return float(max(0.0, min(combined, 1.0)))

    @staticmethod
    def _normalize_iterable(values: Iterable[object]) -> set[str]:
        normalized = set()
        for value in values:
            normalized.add(str(value))
        return normalized

    @staticmethod
    def _extract_source_id(source: dict[str, object]) -> str:
        for key in ("id", "url", "path", "source"):
            value = source.get(key)
            if value:
                return str(value)
        return str(hash(frozenset(source.items())))


class OrchestrationUtils:
    """Collection of static helpers used by the orchestrator."""

    # execution helpers
    get_agent = staticmethod(_get_agent)
    check_agent_can_execute = staticmethod(_check_agent_can_execute)
    deliver_messages = staticmethod(_deliver_messages)
    log_agent_execution = staticmethod(_log_agent_execution)
    call_agent_start_callback = staticmethod(_call_agent_start_callback)
    execute_agent_with_token_counting = staticmethod(_execute_agent_with_token_counting)
    handle_agent_completion = staticmethod(_handle_agent_completion)
    log_sources = staticmethod(_log_sources)
    persist_claims = staticmethod(_persist_claims)
    handle_agent_error = staticmethod(_handle_agent_error)

    # error handling helpers
    categorize_error = staticmethod(_categorize_error)
    apply_recovery_strategy = staticmethod(_apply_recovery_strategy)

    # core execution flows
    execute_agent = staticmethod(_execute_agent)
    execute_cycle = staticmethod(_execute_cycle)
    execute_cycle_async = staticmethod(_execute_cycle_async)
    rotate_list = staticmethod(_rotate_list)
    apply_adaptive_token_budget = staticmethod(_apply_adaptive_token_budget)

    # utility functions
    get_memory_usage = staticmethod(get_memory_usage)
    calculate_result_confidence = staticmethod(calculate_result_confidence)
    capture_token_usage = staticmethod(_capture_token_usage)
    execute_with_adapter = staticmethod(_execute_with_adapter)

    @staticmethod
    def create_scout_gate_policy(config: ConfigModel) -> ScoutGatePolicy:
        """Return a :class:`ScoutGatePolicy` configured for ``config``."""

        return ScoutGatePolicy(config)

    @staticmethod
    def evaluate_scout_gate_policy(
        query: str,
        config: ConfigModel,
        state: QueryState,
        loops: int,
        metrics: OrchestrationMetrics,
    ) -> ScoutGateDecision:
        """Evaluate and return the scout gate decision."""

        policy = ScoutGatePolicy(config)
        return policy.evaluate(query=query, state=state, loops=loops, metrics=metrics)
