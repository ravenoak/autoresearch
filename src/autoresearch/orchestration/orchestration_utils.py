"""Utility helpers for orchestration components.

This module groups functions that were previously attached dynamically to
:class:`~autoresearch.orchestration.orchestrator.Orchestrator`. Keeping them in a
separate utility class makes the helpers easier to import directly in tests and
other modules without relying on dynamic attribute assignment.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from itertools import combinations
from statistics import mean
from typing import Iterable, Mapping, Sequence, Literal, overload

from ..config.models import ConfigModel
from ..logging_utils import get_logger
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
from .model_routing import evaluate_gate_confidence_escalations
from .state import QueryState
from .token_utils import _capture_token_usage, _execute_with_adapter
from .utils import calculate_result_confidence, get_memory_usage


log = get_logger(__name__)


@dataclass
class ScoutGateDecision:
    """Decision emitted by :class:`ScoutGatePolicy`."""

    should_debate: bool
    target_loops: int
    heuristics: dict[str, float]
    thresholds: dict[str, float]
    reason: str
    tokens_saved: int
    rationales: dict[str, dict[str, object]] = field(default_factory=dict)
    telemetry: dict[str, object] = field(default_factory=dict)


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
            "coverage_gap": getattr(self.config, "gate_coverage_gap_threshold", 0.25),
            "retrieval_confidence": getattr(
                self.config, "gate_retrieval_confidence_threshold", 0.5
            ),
            "graph_contradiction": getattr(
                self.config, "gate_graph_contradiction_threshold", 0.25
            ),
            "graph_similarity": getattr(
                self.config, "gate_graph_similarity_threshold", 0.0
            ),
            "scout_agreement": getattr(
                self.config, "gate_scout_agreement_threshold", 0.7
            ),
        }

        graph_contradiction = 0.0
        graph_similarity = 0.0
        graph_metadata: dict[str, object] = {}
        graph_summary: dict[str, object] = {}
        try:
            search_context = SearchContext.get_instance()
        except Exception:
            search_context = None
        if search_context is not None:
            try:
                graph_contradiction = float(search_context.get_contradiction_signal())
            except Exception:
                graph_contradiction = 0.0
            try:
                graph_similarity = float(search_context.get_similarity_signal())
            except Exception:
                graph_similarity = 0.0
            try:
                graph_metadata = search_context.get_graph_stage_metadata()
            except Exception:
                graph_metadata = {}
            try:
                graph_summary = search_context.get_graph_summary()
            except Exception:
                graph_summary = {}

        coverage_gap, coverage_details = self._coverage_gap(state, details=True)
        coverage_snapshot: dict[str, int | float] = dict(coverage_details)
        coverage_ratio = float(max(0.0, min(1.0, 1.0 - coverage_gap)))
        coverage_snapshot["coverage_ratio"] = coverage_ratio
        retrieval_confidence, confidence_details = self._retrieval_confidence(
            state, details=True
        )
        nli_conflict, conflict_details = self._nli_conflict(state, details=True)

        agreement_result = self._scout_agreement(state, details=True)
        if isinstance(agreement_result, tuple):
            agreement_score, agreement_details = agreement_result
        else:
            agreement_score, agreement_details = agreement_result, {}
        agreement_snapshot: dict[str, object] = dict(agreement_details)
        agreement_snapshot.setdefault("score", float(agreement_score))
        agreement_snapshot.setdefault("mean", float(agreement_score))
        agreement_snapshot.setdefault("sample_count", 0)
        if "pairwise_scores" not in agreement_snapshot:
            agreement_snapshot["pairwise_scores"] = []

        heuristics = {
            "retrieval_overlap": self._retrieval_overlap(state),
            "nli_conflict": nli_conflict,
            "complexity": self._complexity(query, state),
            "coverage_gap": coverage_gap,
            "retrieval_confidence": retrieval_confidence,
            "graph_contradiction": graph_contradiction,
            "graph_similarity": graph_similarity,
            "scout_agreement": agreement_score,
        }

        baseline_heuristics = dict(heuristics)

        graph_contradiction_details: dict[str, object] = {}
        contradictions_raw = graph_metadata.get("contradictions")
        if isinstance(contradictions_raw, Mapping):
            graph_contradiction_details = dict(contradictions_raw)
        graph_similarity_details: dict[str, object] = {}
        similarity_raw = graph_metadata.get("similarity")
        if isinstance(similarity_raw, Mapping):
            graph_similarity_details = dict(similarity_raw)

        search_strategy: dict[str, object] = {}
        if getattr(self.config, "gate_capture_query_strategy", True) and search_context is not None:
            try:
                strategy_snapshot = search_context.get_search_strategy()
            except Exception:
                strategy_snapshot = {}
            if strategy_snapshot:
                search_strategy = strategy_snapshot
        if not search_strategy and search_context is not None:
            try:
                metadata_strategy = search_context.get_scout_metadata().get("search_strategy")
            except Exception:
                metadata_strategy = None
            if isinstance(metadata_strategy, Mapping) and metadata_strategy:
                search_strategy = dict(metadata_strategy)
        if not search_strategy:
            metadata_strategy = state.metadata.get("search_strategy")
            if isinstance(metadata_strategy, Mapping) and metadata_strategy:
                search_strategy = dict(metadata_strategy)

        self_critique_markers: dict[str, object] = {}
        if getattr(self.config, "gate_capture_self_critique", True) and search_context is not None:
            try:
                markers_snapshot = search_context.get_self_critique_markers()
            except Exception:
                markers_snapshot = {}
            if markers_snapshot:
                self_critique_markers = markers_snapshot
        if not self_critique_markers and search_context is not None:
            try:
                metadata_markers = search_context.get_scout_metadata().get("search_self_critique")
            except Exception:
                metadata_markers = None
            if isinstance(metadata_markers, Mapping) and metadata_markers:
                self_critique_markers = dict(metadata_markers)
        if not self_critique_markers:
            metadata_markers = state.metadata.get("search_self_critique")
            if isinstance(metadata_markers, Mapping) and metadata_markers:
                self_critique_markers = dict(metadata_markers)

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

        rationales = self._build_rationales(
            heuristics,
            thresholds,
            signal_overrides,
            baseline_heuristics,
            {
                "retrieval_overlap": {
                    "retrieval_sets": len(
                        state.metadata.get("scout_retrieval_sets") or []
                    ),
                    "source_count": len(state.sources),
                },
                "coverage_gap": coverage_snapshot,
                "retrieval_confidence": confidence_details,
                "nli_conflict": conflict_details,
                "graph_contradiction": graph_contradiction_details,
                "graph_similarity": graph_similarity_details,
                "scout_agreement": agreement_snapshot,
            },
        )

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

        graph_telemetry: dict[str, object] = {}
        if graph_contradiction_details:
            graph_telemetry["contradictions"] = graph_contradiction_details
        if graph_similarity_details:
            graph_telemetry["similarity"] = graph_similarity_details
        neighbors = graph_metadata.get("neighbors")
        if neighbors:
            graph_telemetry["neighbors"] = neighbors
        paths = graph_metadata.get("paths")
        if paths:
            graph_telemetry["paths"] = paths
        sources = graph_summary.get("sources")
        if isinstance(sources, Sequence):
            graph_telemetry["sources"] = list(sources)
        provenance = graph_summary.get("provenance")
        if isinstance(provenance, Sequence):
            graph_telemetry["provenance"] = list(provenance)

        telemetry = {
            "coverage": coverage_snapshot,
            "coverage_ratio": coverage_ratio,
            "retrieval_confidence": confidence_details,
            "contradiction_total": conflict_details.get("total", 0.0),
            "contradiction_samples": conflict_details.get("sample_size", 0),
        }
        if graph_telemetry:
            telemetry["graph"] = graph_telemetry
        telemetry["scout_agreement"] = agreement_snapshot
        if search_strategy:
            telemetry["search_strategy"] = search_strategy
        if self_critique_markers:
            telemetry["search_self_critique"] = self_critique_markers

        evaluate_gate_confidence_escalations(
            config=self.config,
            metrics=metrics,
            heuristics=heuristics,
        )

        telemetry["decision_outcome"] = "debate" if should_debate else "scout_exit"

        decision = ScoutGateDecision(
            should_debate=should_debate,
            target_loops=target_loops,
            heuristics=heuristics,
            thresholds=thresholds,
            reason=reason,
            tokens_saved=tokens_saved,
            rationales=rationales,
            telemetry=telemetry,
        )
        metrics.record_gate_decision(decision)
        state.metadata["scout_gate"] = asdict(decision)

        scout_stage = state.metadata.setdefault("scout_stage", {})
        scout_stage["heuristics"] = heuristics
        scout_stage["rationales"] = rationales
        scout_stage["coverage"] = coverage_snapshot
        scout_stage["retrieval_confidence"] = confidence_details
        scout_stage["agreement"] = agreement_snapshot
        if graph_telemetry:
            scout_stage["graph_context"] = graph_telemetry
        if search_strategy:
            scout_stage["search_strategy"] = search_strategy
        if self_critique_markers:
            scout_stage["search_self_critique"] = self_critique_markers
        if state.sources:
            scout_stage["snippets"] = [
                {
                    "source_id": source.get("source_id"),
                    "title": source.get("title"),
                    "url": source.get("url"),
                    "snippet": source.get("snippet"),
                    "backend": source.get("backend"),
                }
                for source in state.sources[:5]
                if isinstance(source, dict)
            ]
        return decision

    def _auto_decide(self, heuristics: dict[str, float], thresholds: dict[str, float]) -> bool:
        """Return ``True`` when multi-loop debate should proceed."""

        # Debate when evidence coverage looks insufficient or uncertainty is high.
        overlap_low = heuristics["retrieval_overlap"] < thresholds["retrieval_overlap"]
        conflict_high = heuristics["nli_conflict"] >= thresholds["nli_conflict"]
        complexity_high = heuristics["complexity"] >= thresholds["complexity"]
        coverage_gap_high = heuristics["coverage_gap"] >= thresholds["coverage_gap"]
        confidence_low = (
            heuristics["retrieval_confidence"] < thresholds["retrieval_confidence"]
        )
        graph_conflict_high = (
            heuristics.get("graph_contradiction", 0.0)
            >= thresholds.get("graph_contradiction", 1.0)
        )
        similarity_threshold = thresholds.get("graph_similarity")
        graph_similarity_low = False
        if similarity_threshold is not None:
            graph_similarity_low = heuristics.get("graph_similarity", 1.0) < similarity_threshold
        agreement_threshold = thresholds.get("scout_agreement")
        scout_disagreement = False
        if agreement_threshold is not None:
            scout_disagreement = (
                heuristics.get("scout_agreement", 1.0) < agreement_threshold
            )
        return (
            overlap_low
            or conflict_high
            or complexity_high
            or coverage_gap_high
            or confidence_low
            or graph_conflict_high
            or graph_similarity_low
            or scout_disagreement
        )

    def _estimate_tokens_saved(self, loops: int, target_loops: int) -> int:
        """Estimate tokens saved when reducing debate loops."""

        if loops <= target_loops:
            return 0
        budget_value = getattr(self.config, "token_budget", None)
        if not isinstance(budget_value, (int, float)):
            return 0
        per_loop = max(1, int(budget_value) // max(1, loops))
        return int(loops - target_loops) * per_loop

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

    @overload
    def _nli_conflict(
        self, state: QueryState, *, details: Literal[True]
    ) -> tuple[float, dict[str, float | int]]:
        ...

    @overload
    def _nli_conflict(
        self, state: QueryState, *, details: Literal[False] = False
    ) -> float:
        ...

    def _nli_conflict(
        self, state: QueryState, *, details: bool = False
    ) -> float | tuple[float, dict[str, float | int]]:
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
        if values:
            average = float(mean(values))
            payload = {
                "total": float(sum(values)),
                "sample_size": len(values),
                "max": float(max(values)),
            }
        else:
            average = 0.0
            payload = {"total": 0.0, "sample_size": 0, "max": 0.0}
        if details:
            return average, payload
        return average

    @overload
    def _coverage_gap(
        self, state: QueryState, *, details: Literal[True]
    ) -> tuple[float, dict[str, int]]:
        ...

    @overload
    def _coverage_gap(
        self, state: QueryState, *, details: Literal[False] = False
    ) -> float:
        ...

    def _coverage_gap(
        self, state: QueryState, *, details: bool = False
    ) -> float | tuple[float, dict[str, int]]:
        """Estimate coverage delta between claims and audits."""

        total_claims = len(state.claims)
        unique_audits = {
            str(audit.get("claim_id"))
            for audit in state.claim_audits
            if isinstance(audit, dict) and audit.get("claim_id")
        }
        audited_claims = len(unique_audits)
        coverage_ratio = 1.0 if total_claims == 0 else audited_claims / total_claims
        gap = float(max(0.0, min(1.0, 1.0 - coverage_ratio)))
        payload = {
            "total_claims": total_claims,
            "audited_claims": audited_claims,
            "audit_records": len(state.claim_audits),
        }
        if details:
            return gap, payload
        return gap

    @overload
    def _retrieval_confidence(
        self, state: QueryState, *, details: Literal[True]
    ) -> tuple[float, dict[str, float | int]]:
        ...

    @overload
    def _retrieval_confidence(
        self, state: QueryState, *, details: Literal[False] = False
    ) -> float:
        ...

    def _retrieval_confidence(
        self, state: QueryState, *, details: bool = False
    ) -> float | tuple[float, dict[str, float | int]]:
        """Compute retrieval confidence from entailment-derived scores."""

        scores = state.metadata.get("scout_entailment_scores")
        confidences: list[float] = []
        if isinstance(scores, Sequence):
            for item in scores:
                if isinstance(item, dict):
                    candidate = item.get("support") or item.get("score")
                else:
                    candidate = item
                if candidate is None:
                    continue
                try:
                    confidences.append(float(candidate))
                except (TypeError, ValueError):
                    continue
        if confidences:
            average = float(max(0.0, min(1.0, mean(confidences))))
            payload = {
                "sample_size": len(confidences),
                "min": float(min(confidences)),
                "max": float(max(confidences)),
            }
        else:
            average = 0.0
            payload = {"sample_size": 0, "min": 0.0, "max": 0.0}
        if details:
            return average, payload
        return average

    @staticmethod
    def _normalize_answer(text: str) -> set[str]:
        """Return normalized token set for scout agreement calculations."""

        if not isinstance(text, str):
            return set()
        return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if token}

    def _scout_agreement(
        self, state: QueryState, *, details: bool = False
    ) -> float | tuple[float, dict[str, object]]:
        """Estimate agreement across stored scout samples."""

        raw_samples = state.metadata.get("scout_samples")
        samples: list[Mapping[str, object]] = []
        if isinstance(raw_samples, Sequence):
            for entry in raw_samples:
                if isinstance(entry, Mapping):
                    samples.append(entry)

        if not samples:
            score = 1.0
            payload: dict[str, object] = {
                "sample_count": 0,
                "pairwise_scores": [],
                "basis": "answer_claim_tokens",
            }
            return (score, payload) if details else score

        token_sets: list[set[str]] = []
        answers: list[str] = []
        for entry in samples:
            entry_tokens: set[str] = set()
            answer = entry.get("answer")
            if isinstance(answer, str):
                answers.append(answer)
                entry_tokens |= self._normalize_answer(answer)
            claims = entry.get("claims")
            if isinstance(claims, Sequence):
                for claim in claims:
                    if isinstance(claim, Mapping):
                        content = claim.get("content")
                        if isinstance(content, str):
                            entry_tokens |= self._normalize_answer(content)
            token_sets.append(entry_tokens)

        if len(token_sets) <= 1:
            score = 1.0
            payload = {
                "sample_count": len(token_sets),
                "pairwise_scores": [],
                "basis": "answer_claim_tokens",
                "answers": answers,
            }
            return (score, payload) if details else score

        pairwise_scores: list[float] = []
        for left_idx, right_idx in combinations(range(len(token_sets)), 2):
            left_tokens = token_sets[left_idx]
            right_tokens = token_sets[right_idx]
            union = left_tokens | right_tokens
            if not union:
                pairwise_scores.append(1.0)
            else:
                pairwise_scores.append(len(left_tokens & right_tokens) / len(union))

        if pairwise_scores:
            score = float(sum(pairwise_scores) / len(pairwise_scores))
            min_score = float(min(pairwise_scores))
            max_score = float(max(pairwise_scores))
        else:
            score = 1.0
            min_score = 1.0
            max_score = 1.0

        payload = {
            "sample_count": len(token_sets),
            "pairwise_scores": [float(value) for value in pairwise_scores],
            "basis": "answer_claim_tokens",
            "answers": answers,
            "min": min_score,
            "max": max_score,
            "mean": score,
        }

        return (score, payload) if details else score

    def _build_rationales(
        self,
        heuristics: dict[str, float],
        thresholds: dict[str, float],
        overrides: dict[str, object],
        baseline: dict[str, float],
        details: Mapping[str, Mapping[str, object]],
    ) -> dict[str, dict[str, object]]:
        """Produce structured rationales for each gating signal."""

        rules: dict[str, dict[str, str | bool]] = {
            "retrieval_overlap": {
                "direction": "low",
                "description": "Mean overlap across scout retrieval backends",
            },
            "nli_conflict": {
                "direction": "high",
                "description": "Aggregated contradiction probability",
            },
            "complexity": {
                "direction": "high",
                "description": "Query complexity estimate from scout analysis",
            },
            "coverage_gap": {
                "direction": "high",
                "description": "Share of claims lacking audits in scout stage",
            },
            "retrieval_confidence": {
                "direction": "low",
                "description": "Average entailment-backed retrieval confidence",
            },
            "graph_contradiction": {
                "direction": "high",
                "description": "Weighted contradiction signal from the knowledge graph",
            },
            "graph_similarity": {
                "direction": "low",
                "description": "Weighted neighbour density from the knowledge graph",
            },
            "scout_agreement": {
                "direction": "low",
                "description": "Pairwise agreement score across scout samples",
            },
        }

        rationales: dict[str, dict[str, object]] = {}
        for signal, value in heuristics.items():
            rule = rules.get(signal, {})
            direction = rule.get("direction", "high")
            comparator = "<" if direction == "low" else ">="
            threshold = thresholds.get(signal)
            triggered = False
            if threshold is not None:
                if comparator == "<":
                    triggered = value < threshold
                else:
                    triggered = value >= threshold
            rationale: dict[str, object] = {
                "value": value,
                "threshold": threshold,
                "comparator": comparator,
                "triggered": triggered,
                "description": rule.get("description", ""),
                "baseline": baseline.get(signal, value),
            }
            if signal in overrides:
                rationale["override"] = overrides[signal]
            if details.get(signal):
                rationale["details"] = details[signal]
            rationales[signal] = rationale
        return rationales

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
            clause_score = 0.0
            if clauses is not None:
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

        try:
            SearchContext.get_instance().apply_scout_metadata(state)
        except Exception as exc:  # pragma: no cover - defensive logging
            log.debug("Failed to attach scout metadata", exc_info=exc)

        policy = ScoutGatePolicy(config)
        return policy.evaluate(query=query, state=state, loops=loops, metrics=metrics)
