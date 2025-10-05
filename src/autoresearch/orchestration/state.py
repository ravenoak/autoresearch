"""State management for the dialectical reasoning process."""

import re
import time
from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from threading import RLock
from typing import TYPE_CHECKING, Any, Optional, Sequence as SeqType, cast

from pydantic import BaseModel, Field, PrivateAttr

from ..agents.feedback import FeedbackEvent
from ..agents.messages import MessageProtocol
from ..evidence import aggregate_entailment_scores, score_entailment
from ..logging_utils import get_logger
from ..models import QueryResponse
from ..search import Search
from ..search.context import SearchContext
from ..storage import ClaimAuditRecord, ClaimAuditStatus, ensure_source_id
from .task_graph import TaskGraph

LOCK_TYPE = type(RLock())

log = get_logger(__name__)


def _default_task_graph() -> dict[str, Any]:
    """Return an empty task graph structure for planner outputs."""

    return {"tasks": [], "edges": [], "metadata": {}}


if TYPE_CHECKING:  # pragma: no cover
    from ..interfaces import QueryStateLike  # noqa: F401
    PrivateLockAttr = PrivateAttr[RLock]
else:  # pragma: no cover - runtime alias
    PrivateLockAttr = PrivateAttr


@dataclass(slots=True)
class AnswerAuditOutcome:
    """Outcome payload returned by :class:`AnswerAuditor`."""

    answer: str
    reasoning: list[dict[str, Any]]
    claim_audits: list[dict[str, Any]]
    additional_sources: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    warnings: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class _RetryResult:
    """Encapsulate retrieval retries executed during answer auditing."""

    claim_id: str
    record: ClaimAuditRecord
    sources: list[dict[str, Any]]
    result_count: int


class AnswerAuditor:
    """Review claim audits, trigger retries, and hedge unsupported findings."""

    _RETRY_RESULTS = 5

    def __init__(self, state: "QueryState") -> None:
        self._state = state

    def review(self) -> AnswerAuditOutcome:
        """Return a hedged answer, updated claims, and enriched audits."""

        claims = [self._copy_claim(claim) for claim in self._state.claims]
        grouped, audits = self._collect_audits(claims)

        for claim in claims:
            claim_id = str(claim.get("id") or "")
            if not claim_id:
                continue
            status = self._resolve_status(grouped.get(claim_id))
            self._annotate_claim(claim, status)

        retry_records: list[_RetryResult] = []
        retry_failures: list[str] = []

        for claim in claims:
            claim_id = str(claim.get("id") or "")
            if not claim_id:
                continue
            status_token = claim.get("audit_status", ClaimAuditStatus.NEEDS_REVIEW.value)
            try:
                current_status = (
                    status_token
                    if isinstance(status_token, ClaimAuditStatus)
                    else ClaimAuditStatus(str(status_token))
                )
            except ValueError:
                current_status = ClaimAuditStatus.NEEDS_REVIEW
            if current_status is not ClaimAuditStatus.UNSUPPORTED:
                continue
            retry = self._retry_claim(claim, grouped.get(claim_id, []))
            if retry is None:
                retry_failures.append(claim_id)
                continue
            record_payload = retry.record.to_payload()
            audits.append(record_payload)
            grouped.setdefault(claim_id, []).append(record_payload)
            retry_records.append(retry)
            status_after = self._resolve_status(grouped.get(claim_id))
            self._annotate_claim(claim, status_after, record_payload)

        unsupported_after: list[str] = []
        needs_review_after: list[str] = []
        for claim in claims:
            claim_id = str(claim.get("id") or "")
            if not claim_id:
                continue
            status_token = claim.get("audit_status", ClaimAuditStatus.NEEDS_REVIEW.value)
            try:
                status = (
                    status_token
                    if isinstance(status_token, ClaimAuditStatus)
                    else ClaimAuditStatus(str(status_token))
                )
            except ValueError:
                status = ClaimAuditStatus.NEEDS_REVIEW
            if status is ClaimAuditStatus.UNSUPPORTED:
                unsupported_after.append(claim_id)
            elif status is ClaimAuditStatus.NEEDS_REVIEW:
                needs_review_after.append(claim_id)

        answer_text_raw = self._state.results.get("final_answer", "")
        normalized_answer = self._normalize_answer(str(answer_text_raw or ""))
        warning_entries = self._build_warning_entries(
            unsupported_after,
            needs_review_after,
            claims,
        )

        metrics = {
            "unsupported_claims": list(unsupported_after),
            "needs_review_claims": list(needs_review_after),
            "retry_attempts": [
                {
                    "claim_id": retry.claim_id,
                    "status": retry.record.status.value,
                    "sample_size": retry.record.sample_size,
                    "result_count": retry.result_count,
                }
                for retry in retry_records
            ],
            "retry_failures": retry_failures,
        }
        if warning_entries:
            metrics["warnings"] = [dict(entry) for entry in warning_entries]

        return AnswerAuditOutcome(
            answer=normalized_answer,
            reasoning=claims,
            claim_audits=audits,
            additional_sources=self._extract_sources(retry_records),
            metrics=metrics,
            warnings=warning_entries,
        )

    def _copy_claim(self, claim: Mapping[str, Any]) -> dict[str, Any]:
        payload = dict(claim)
        audit = payload.get("audit")
        if isinstance(audit, Mapping):
            payload["audit"] = dict(audit)
        return payload

    def _collect_audits(
        self, claims: Sequence[Mapping[str, Any]]
    ) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        collected: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()

        def _record(payload: Mapping[str, Any]) -> None:
            claim_id_raw = payload.get("claim_id")
            if not claim_id_raw:
                return
            claim_id = str(claim_id_raw)
            audit_payload = dict(payload)
            audit_id = str(audit_payload.get("audit_id") or "")
            key = (claim_id, audit_id)
            if audit_id and key in seen:
                return
            if audit_id:
                seen.add(key)
            collected.append(audit_payload)
            grouped.setdefault(claim_id, []).append(audit_payload)

        for audit in self._state.claim_audits:
            if isinstance(audit, Mapping):
                _record(audit)

        for claim in claims:
            claim_audit = claim.get("audit")
            if isinstance(claim_audit, Mapping):
                _record(claim_audit)

        return grouped, collected

    def _resolve_status(
        self, audits: Optional[Sequence[Mapping[str, Any]]]
    ) -> ClaimAuditStatus:
        if not audits:
            return ClaimAuditStatus.NEEDS_REVIEW
        severity_order = {
            ClaimAuditStatus.SUPPORTED: 0,
            ClaimAuditStatus.NEEDS_REVIEW: 1,
            ClaimAuditStatus.UNSUPPORTED: 2,
        }
        resolved = ClaimAuditStatus.NEEDS_REVIEW
        resolved_score = -1
        for audit in audits:
            status_raw = audit.get("status")
            try:
                status = (
                    status_raw
                    if isinstance(status_raw, ClaimAuditStatus)
                    else ClaimAuditStatus(str(status_raw))
                )
            except ValueError:
                continue
            score = severity_order.get(status, -1)
            if score >= resolved_score:
                resolved = status
                resolved_score = score
        return resolved

    def _annotate_claim(
        self,
        claim: dict[str, Any],
        status: ClaimAuditStatus,
        latest_audit: Mapping[str, Any] | None = None,
    ) -> None:
        claim_id = str(claim.get("id") or "")
        original_content = str(claim.get("content", ""))
        hedged = self._hedged_claim_text(original_content, status)
        claim["hedged_content"] = hedged
        claim["audit_status"] = status.value
        visibility = claim.get("visibility")
        if not isinstance(visibility, Mapping):
            visibility = {}
        visibility = dict(visibility)
        visibility.setdefault("key_findings", status is not ClaimAuditStatus.UNSUPPORTED)
        visibility["reasoning"] = True
        claim["visibility"] = visibility

        audit_payload: dict[str, Any]
        if latest_audit is not None:
            audit_payload = dict(latest_audit)
        else:
            existing = claim.get("audit")
            audit_payload = dict(existing) if isinstance(existing, Mapping) else {}
        audit_payload["claim_id"] = claim_id
        audit_payload["status"] = status.value
        claim["audit"] = audit_payload

    def _hedged_claim_text(
        self, content: str, status: ClaimAuditStatus
    ) -> str:
        cleaned = content.strip()
        if not cleaned:
            return cleaned
        if status is ClaimAuditStatus.UNSUPPORTED:
            return f"⚠️ Unsupported: {cleaned}"
        if status is ClaimAuditStatus.NEEDS_REVIEW:
            return f"⚠️ Needs review: {cleaned}"
        return cleaned

    def _normalize_answer(self, answer: str) -> str:
        """Return ``answer`` when provided, otherwise a fallback string."""

        if answer and answer.strip():
            return answer
        return "No answer synthesized"

    def _build_warning_entries(
        self,
        unsupported: Sequence[str],
        needs_review: Sequence[str],
        claims: Sequence[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """Construct structured warning payloads for downstream consumers."""

        entries: list[dict[str, Any]] = []
        if unsupported:
            entries.append(
                self._format_warning_entry(
                    code="answer_audit.unsupported_claims",
                    message="Unsupported claims remain after retries",
                    severity="warning",
                    claim_ids=unsupported,
                    claims=claims,
                )
            )
        elif needs_review:
            entries.append(
                self._format_warning_entry(
                    code="answer_audit.needs_review_claims",
                    message="Some claims still require review",
                    severity="warning",
                    claim_ids=needs_review,
                    claims=claims,
                )
            )
        return entries

    def _format_warning_entry(
        self,
        *,
        code: str,
        message: str,
        severity: str,
        claim_ids: Sequence[str],
        claims: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Return a structured warning entry with claim labels."""

        labels = self._summarise_claims(claim_ids, claims)
        structured_claims: list[dict[str, Any]] = []
        for index, claim_id in enumerate(claim_ids):
            label = labels[index] if index < len(labels) else str(claim_id)
            structured_claims.append({
                "id": str(claim_id),
                "label": label,
            })
        return {
            "code": code,
            "message": message,
            "severity": severity,
            "claim_ids": [str(cid) for cid in claim_ids],
            "claims": structured_claims,
        }

    def _summarise_claims(
        self, claim_ids: Sequence[str], claims: Sequence[Mapping[str, Any]]
    ) -> list[str]:
        lookup = {str(claim.get("id")): str(claim.get("content", "")) for claim in claims}
        labels: list[str] = []
        for claim_id in claim_ids:
            content = lookup.get(str(claim_id), "")
            labels.append(self._shorten(content) or str(claim_id))
        return labels

    def _shorten(self, text: str, max_length: int = 60) -> str:
        cleaned = " ".join(text.split())
        if len(cleaned) <= max_length:
            return cleaned
        return cleaned[: max_length - 1].rstrip() + "…"

    def _retry_claim(
        self,
        claim: Mapping[str, Any],
        existing_audits: Sequence[Mapping[str, Any]],
    ) -> _RetryResult | None:
        claim_id = str(claim.get("id") or "")
        hypothesis = str(claim.get("content", "")).strip()
        if not claim_id or not hypothesis:
            return None

        try:
            lookup = Search.external_lookup(
                hypothesis,
                max_results=self._RETRY_RESULTS,
                return_handles=True,
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            log.debug("Answer audit retry failed for %s: %s", claim_id, exc)
            return None

        if isinstance(lookup, list):
            candidates = list(lookup)
            handle_payload: dict[str, Any] | None = None
        else:
            candidates = list(getattr(lookup, "results", []))
            cache = getattr(getattr(lookup, "cache", None), "namespace", None)
            handle_payload = {"cache_namespace": cache} if cache else None

        if not candidates:
            provenance = {
                "retrieval": {
                    "mode": "answer_audit.retry",
                    "query": hypothesis,
                    "base_query": self._state.query,
                    "events": [
                        {
                            "variant": "audit_retry",
                            "result_count": 0,
                            "claim_id": claim_id,
                        }
                    ],
                    "handle": handle_payload,
                },
                "backoff": {"retry_count": len(existing_audits)},
                "evidence": {"source_ids": []},
            }
            record = ClaimAuditRecord.from_score(
                claim_id,
                None,
                status=ClaimAuditStatus.UNSUPPORTED,
                notes="Targeted re-retrieval returned no evidence.",
                provenance=provenance,
            )
            return _RetryResult(claim_id, record, [], 0)

        scored_sources: list[tuple[float, dict[str, Any]]] = []
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                continue
            source = ensure_source_id(candidate)
            snippet = (
                str(source.get("snippet") or source.get("content") or "").strip()
            )
            if not snippet:
                continue
            breakdown = score_entailment(hypothesis, snippet)
            scored_sources.append((breakdown.score, source))

        breakdowns = [score for score, _ in scored_sources]
        aggregate = aggregate_entailment_scores(breakdowns)
        best_sources = [src for _, src in sorted(scored_sources, reverse=True)[:2]]

        provenance = {
            "retrieval": {
                "mode": "answer_audit.retry",
                "query": hypothesis,
                "base_query": self._state.query,
                "events": [
                    {
                        "variant": "audit_retry",
                        "result_count": len(candidates),
                        "claim_id": claim_id,
                    }
                ],
                "handle": handle_payload,
            },
            "backoff": {
                "retry_count": len(existing_audits),
                "paraphrases": [],
            },
            "evidence": {
                "source_ids": [src.get("source_id") for src in best_sources],
            },
        }

        if aggregate.sample_size:
            note = (
                f"Retry entailment from {aggregate.sample_size} snippet(s). "
                f"Variance={aggregate.variance:.3f}."
            )
        else:
            note = "Retry entailment could not score evidence."

        status = ClaimAuditStatus.UNSUPPORTED
        if aggregate.sample_size:
            status = ClaimAuditStatus.from_entailment(aggregate.mean)
            if aggregate.disagreement and status is ClaimAuditStatus.SUPPORTED:
                status = ClaimAuditStatus.NEEDS_REVIEW

        record = ClaimAuditRecord.from_score(
            claim_id,
            aggregate.mean if aggregate.sample_size else None,
            sources=best_sources,
            notes=note,
            status=status,
            variance=aggregate.variance if aggregate.sample_size else None,
            instability=aggregate.disagreement if aggregate.sample_size else None,
            sample_size=aggregate.sample_size or None,
            provenance=provenance,
        )
        return _RetryResult(claim_id, record, best_sources, len(candidates))

    def _extract_sources(self, retries: Sequence[_RetryResult]) -> list[dict[str, Any]]:
        collected: dict[str, dict[str, Any]] = {}
        for retry in retries:
            for source in retry.sources:
                source_id = str(source.get("source_id") or "")
                collected[source_id or str(id(source))] = dict(source)
        return list(collected.values())


class QueryState(BaseModel):
    """State object passed between agents during dialectical cycles.

    Implements :class:`~autoresearch.interfaces.QueryStateLike`.
    """

    query: str
    claims: list[dict[str, Any]] = Field(default_factory=list)
    claim_audits: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    results: dict[str, Any] = Field(default_factory=dict)
    messages: list[dict[str, Any]] = Field(default_factory=list)
    feedback_events: list[FeedbackEvent] = Field(default_factory=list)
    coalitions: dict[str, list[str]] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    task_graph: dict[str, Any] = Field(default_factory=_default_task_graph)
    react_log: list[dict[str, Any]] = Field(default_factory=list)
    react_traces: list[dict[str, Any]] = Field(default_factory=list)
    cycle: int = 0
    primus_index: int = 0
    last_updated: float = Field(default_factory=time.time)
    error_count: int = 0

    _lock: PrivateLockAttr = cast(PrivateLockAttr, PrivateAttr(default_factory=RLock))

    def model_copy(
        self,
        *,
        update: Mapping[str, Any] | None = None,
        deep: bool | None = None,
        memo: dict[int, Any] | None = None,
    ) -> "QueryState":
        """Return a copy of the state without cloning synchronization primitives."""

        sanitized_update: dict[str, Any] | None = None
        if update:
            sanitized_update = {
                key: value for key, value in update.items() if key != "_lock"
            }

        data = self.model_dump(mode="python")
        if sanitized_update:
            data = {**data, **sanitized_update}

        original_lock = getattr(self, "_lock", None)
        effective_memo: dict[int, Any] | None = None
        if deep:
            effective_memo = dict(memo or {})
            for value in self.__dict__.values():
                if isinstance(value, LOCK_TYPE):
                    effective_memo.setdefault(id(value), value)
            data = deepcopy(data, effective_memo)

        copied = self.__class__.model_validate(data)
        copied._ensure_lock()

        if deep and isinstance(original_lock, LOCK_TYPE):
            copied_lock = getattr(copied, "_lock", None)
            if copied_lock is original_lock:
                object.__setattr__(copied, "_lock", RLock())

        return copied

    def model_post_init(self, __context: Any) -> None:
        """Ensure synchronization primitives survive model cloning."""
        super().model_post_init(__context)
        self._ensure_lock()

    def update(self, result: Mapping[str, object]) -> None:
        """Update state with agent result."""
        with self._lock:
            claims_obj = result.get("claims")
            if claims_obj is not None:
                if not isinstance(claims_obj, Sequence) or isinstance(
                    claims_obj, (str, bytes)
                ):
                    raise TypeError("claims must be a sequence of mappings")
                for claim in claims_obj:
                    if not isinstance(claim, Mapping):
                        raise TypeError("each claim must be a mapping")
                    claim_dict = dict(claim)
                    self.claims.append(claim_dict)
                    audit_payload = claim_dict.get("audit")
                    if isinstance(audit_payload, Mapping):
                        self.claim_audits.append(dict(audit_payload))

            sources_obj = result.get("sources")
            if sources_obj is not None:
                if not isinstance(sources_obj, Sequence) or isinstance(
                    sources_obj, (str, bytes)
                ):
                    raise TypeError("sources must be a sequence of mappings")
                for source in sources_obj:
                    if not isinstance(source, Mapping):
                        raise TypeError("each source must be a mapping")
                    self.sources.append(dict(source))

            metadata_obj = result.get("metadata")
            if metadata_obj is not None:
                if not isinstance(metadata_obj, Mapping):
                    raise TypeError("metadata must be a mapping")
                for key, value in metadata_obj.items():
                    self.metadata[key] = value
            # Update results with agent-specific outputs
            results_obj = result.get("results")
            if results_obj is not None:
                if not isinstance(results_obj, Mapping):
                    raise TypeError("results must be a mapping")
                self.results.update(results_obj)
                task_graph_obj = results_obj.get("task_graph")
                if task_graph_obj is not None:
                    self.set_task_graph(task_graph_obj)

            audits_obj = result.get("claim_audits")
            if audits_obj is not None:
                if not isinstance(audits_obj, Sequence) or isinstance(
                    audits_obj, (str, bytes)
                ):
                    raise TypeError("claim_audits must be a sequence of mappings")
                for audit in audits_obj:
                    if not isinstance(audit, Mapping):
                        raise TypeError("each claim_audit must be a mapping")
                    self.claim_audits.append(dict(audit))
            react_traces_obj = result.get("react_traces")
            if react_traces_obj is not None:
                self.extend_react_traces(react_traces_obj)
            # Update timestamp
            self.last_updated = time.time()

    def add_error(self, error_info: dict[str, Any]) -> None:
        """Track execution errors."""
        with self._lock:
            self.error_count += 1
            if "errors" not in self.metadata:
                self.metadata["errors"] = []
            self.metadata["errors"].append(error_info)

    def add_message(self, message: dict[str, Any]) -> None:
        """Store a message exchanged between agents."""
        with self._lock:
            self.messages.append(message)

    def add_feedback_event(self, event: FeedbackEvent) -> None:
        """Store a feedback event exchanged between agents."""
        with self._lock:
            self.feedback_events.append(event)

    def get_feedback_events(self, *, recipient: Optional[str] = None) -> list[FeedbackEvent]:
        """Retrieve feedback events for a specific recipient."""
        with self._lock:
            events = list(self.feedback_events)
        if recipient is not None:
            events = [e for e in events if e.target == recipient]
        return events

    def set_task_graph(self, task_graph: Any) -> list[dict[str, Any]]:
        """Store the structured planner output for downstream coordination."""

        with self._lock:
            top_level = self._extract_planner_top_level(task_graph)
            normalized, warnings = self._normalise_task_graph(task_graph)
            self.task_graph = normalized
            planner_meta = self.metadata.setdefault("planner", {})
            stats = {
                "task_count": len(normalized.get("tasks", [])),
                "edge_count": len(normalized.get("edges", [])),
                "updated_at": time.time(),
            }
            planner_meta["task_graph"] = stats
            telemetry = self._planner_telemetry_snapshot(normalized, top_level)
            if telemetry["tasks"] or telemetry.get("objectives") or telemetry.get("exit_criteria"):
                existing = planner_meta.get("telemetry")
                merged: dict[str, Any] = {}
                if isinstance(existing, Mapping):
                    merged.update(existing)
                merged.update(telemetry)
                planner_meta["telemetry"] = merged
                self.add_react_log_entry(
                    "planner.telemetry",
                    {
                        "telemetry": merged,
                        "task_graph_stats": stats,
                    },
                )
            if warnings:
                self.add_react_log_entry(
                    "planner.normalization",
                    {
                        "warnings": list(warnings),
                        "task_graph_stats": stats,
                    },
                )
        return warnings

    def add_react_log_entry(
        self,
        event: str,
        payload: Mapping[str, Any],
        *,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:
        """Append a structured entry to the ReAct event log."""

        entry = {
            "event": event,
            "payload": dict(payload),
            "metadata": dict(metadata) if metadata else {},
            "cycle": self.cycle,
            "timestamp": time.time(),
        }
        with self._lock:
            self.react_log.append(entry)
        return entry

    def record_planner_trace(
        self,
        *,
        prompt: str,
        raw_response: str,
        normalized: Mapping[str, Any],
        warnings: SeqType[Mapping[str, Any] | str] | None = None,
    ) -> dict[str, Any]:
        """Record planner prompt/response pairs for replay."""

        warning_payload: list[dict[str, Any]] = []
        for warning in warnings or []:
            if isinstance(warning, Mapping):
                warning_payload.append(dict(warning))
            else:
                warning_payload.append({"message": str(warning)})
        return self.add_react_log_entry(
            "planner.trace",
            {
                "prompt": prompt,
                "raw_response": raw_response,
                "task_graph": dict(normalized),
            },
            metadata={"warnings": warning_payload} if warning_payload else None,
        )

    def extend_react_traces(self, traces: Any) -> None:
        """Append a batch of ReAct traces captured during execution."""

        if isinstance(traces, Mapping):
            iterable = [traces]
        else:
            iterable = list(traces or [])

        with self._lock:
            for trace in iterable:
                if not isinstance(trace, Mapping):
                    raise TypeError("each react trace must be a mapping")
                self.react_traces.append(dict(trace))

    def add_react_trace(self, trace: Mapping[str, Any]) -> None:
        """Append a single ReAct trace entry."""

        self.extend_react_traces([trace])

    def get_react_traces(self, *, task_id: Optional[str] = None) -> list[dict[str, Any]]:
        """Retrieve ReAct traces, optionally filtered by task id."""

        with self._lock:
            traces = list(self.react_traces)
        if task_id is not None:
            traces = [trace for trace in traces if trace.get("task_id") == task_id]
        return traces

    def _normalise_task_graph(
        self, task_graph: Any
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Validate and normalise a task graph payload."""

        warnings: list[dict[str, Any]] = []
        payload: dict[str, Any]
        if isinstance(task_graph, TaskGraph):
            payload = dict(task_graph.to_payload())
        elif isinstance(task_graph, Mapping):
            payload = dict(task_graph)
        elif isinstance(task_graph, Sequence) and not isinstance(task_graph, (str, bytes)):
            payload = {"tasks": list(task_graph)}
        else:
            raise TypeError("task_graph must be a mapping or sequence")

        tasks_obj = payload.get("tasks", [])
        edges_obj = payload.get("edges", [])
        metadata_obj = payload.get("metadata", {})

        if not isinstance(tasks_obj, Sequence) or isinstance(tasks_obj, (str, bytes)):
            raise TypeError("task_graph['tasks'] must be a sequence")
        if not isinstance(edges_obj, Sequence) or isinstance(edges_obj, (str, bytes)):
            raise TypeError("task_graph['edges'] must be a sequence")
        if not isinstance(metadata_obj, Mapping):
            raise TypeError("task_graph['metadata'] must be a mapping")

        normalized_tasks: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for idx, task in enumerate(tasks_obj, start=1):
            if not isinstance(task, Mapping):
                raise TypeError("each task must be a mapping")
            task_id = str(task.get("id") or f"task-{idx}")
            if task_id in seen_ids:
                warnings.append(
                    self._task_graph_warning(
                        "state.duplicate_task_id",
                        "Duplicate task identifier encountered.",
                        task_id=task_id,
                    )
                )
            seen_ids.add(task_id)
            question = str(
                task.get("question")
                or task.get("goal")
                or task.get("description")
                or task.get("prompt")
                or ""
            ).strip()
            if not question:
                warnings.append(
                    self._task_graph_warning(
                        "state.missing_question",
                        "Task missing question text after normalisation.",
                        task_id=task_id,
                    )
                )
            tools = self._ensure_list_of_str(
                task.get("tools"),
                field="tools",
                task_id=task_id,
                warnings=warnings,
                split_pattern=r",|;|/| and ",
            )
            depends_on = self._ensure_list_of_str(
                task.get("depends_on"),
                field="depends_on",
                task_id=task_id,
                warnings=warnings,
                split_pattern=r",|;",
            )
            criteria = self._ensure_list_of_str(
                task.get("criteria") or task.get("exit_criteria"),
                field="criteria",
                task_id=task_id,
                warnings=warnings,
                split_pattern=r",|;",
            )
            sub_questions = self._ensure_list_of_str(
                task.get("sub_questions") or task.get("objectives"),
                field="sub_questions",
                task_id=task_id,
                warnings=warnings,
            )
            affinity_raw = task.get("affinity") or task.get("tool_affinity")
            affinity: dict[str, float] = {}
            if isinstance(affinity_raw, Mapping):
                for tool, value in affinity_raw.items():
                    try:
                        affinity[str(tool)] = float(value)
                    except (TypeError, ValueError):
                        warnings.append(
                            self._task_graph_warning(
                                "state.affinity_cast_failed",
                                "Affinity score is not numeric.",
                                task_id=task_id,
                                detail={"tool": str(tool), "value": value},
                            )
                        )
            elif affinity_raw not in (None, {}):
                warnings.append(
                    self._task_graph_warning(
                        "state.affinity_invalid",
                        "Affinity payload must be a mapping of tool->score.",
                        task_id=task_id,
                        detail={"affinity": affinity_raw},
                    )
                )
            depth_value = task.get("dependency_depth")
            if depth_value is None:
                depth_value = task.get("depth")
            dependency_depth = self._coerce_optional_int(
                depth_value,
                field="dependency_depth",
                task_id=task_id,
                warnings=warnings,
            )
            dependency_rationale = self._coerce_optional_text(
                task.get("dependency_rationale") or task.get("dependency_note"),
                field="dependency_rationale",
                task_id=task_id,
                warnings=warnings,
            )
            socratic_checks = self._coerce_socratic_checks(
                task.get("socratic_checks") or task.get("self_check"),
                field="socratic_checks",
                task_id=task_id,
                warnings=warnings,
            )
            metadata_payload = task.get("metadata")
            if isinstance(metadata_payload, Mapping):
                metadata = dict(metadata_payload)
            elif metadata_payload is None:
                metadata = {}
            else:
                metadata = {}
                warnings.append(
                    self._task_graph_warning(
                        "state.metadata_invalid",
                        "Task metadata payload must be a mapping.",
                        task_id=task_id,
                        detail={"metadata": metadata_payload},
                    )
                )
            explanation_value = task.get("explanation")
            explanation: str | None = None
            if isinstance(explanation_value, str):
                explanation = explanation_value.strip() or None

            normalized_task: dict[str, Any] = {
                "id": task_id,
                "question": question,
                "tools": tools,
                "depends_on": depends_on,
                "criteria": criteria,
                "affinity": affinity,
                "metadata": metadata,
            }
            if sub_questions:
                normalized_task["sub_questions"] = sub_questions
            if explanation:
                normalized_task["explanation"] = explanation
            if dependency_depth is not None:
                normalized_task["dependency_depth"] = dependency_depth
            if dependency_rationale:
                normalized_task["dependency_rationale"] = dependency_rationale
            if socratic_checks:
                normalized_task["socratic_checks"] = socratic_checks
            normalized_tasks.append(normalized_task)

        valid_ids = {task["id"] for task in normalized_tasks}
        for task in normalized_tasks:
            filtered_deps: list[str] = []
            for dep in task.get("depends_on", []):
                if dep in valid_ids:
                    filtered_deps.append(dep)
                else:
                    warnings.append(
                        self._task_graph_warning(
                            "state.dependency_missing",
                            "Dependency references unknown task id.",
                            task_id=task["id"],
                            detail={"dependency": dep},
                        )
                    )
            task["depends_on"] = filtered_deps

        normalized_edges: list[dict[str, Any]] = []
        edge_signatures: set[tuple[str, str, str]] = set()
        for edge in edges_obj:
            if not isinstance(edge, Mapping):
                raise TypeError("each edge must be a mapping")
            source = str(edge.get("source"))
            target = str(edge.get("target"))
            edge_type = str(edge.get("type", "dependency"))
            if source not in valid_ids or target not in valid_ids:
                warnings.append(
                    self._task_graph_warning(
                        "state.edge_missing_task",
                        "Edge references unknown task id.",
                        detail={"source": source, "target": target},
                    )
                )
                continue
            signature = (source, target, edge_type)
            if signature in edge_signatures:
                continue
            edge_signatures.add(signature)
            normalized_edges.append(
                {"source": source, "target": target, "type": edge_type}
            )

        for task in normalized_tasks:
            for dep in task.get("depends_on", []):
                signature = (dep, task["id"], "dependency")
                if signature not in edge_signatures:
                    edge_signatures.add(signature)
                    normalized_edges.append(
                        {"source": dep, "target": task["id"], "type": "dependency"}
                    )

        metadata_copy = dict(metadata_obj)
        metadata_copy.setdefault("version", 1)
        dependency_overview = self._coerce_dependency_overview(
            payload.get("dependency_overview") or metadata_copy.get("dependency_overview"),
            warnings=warnings,
        )
        if dependency_overview:
            metadata_copy["dependency_overview"] = dependency_overview

        return {
            "tasks": normalized_tasks,
            "edges": normalized_edges,
            "metadata": metadata_copy,
        }, warnings

    def _ensure_list_of_str(
        self,
        value: Any,
        *,
        field: str,
        task_id: str,
        warnings: list[dict[str, Any]],
        split_pattern: str | None = None,
    ) -> list[str]:
        """Coerce ``value`` into a list of strings with optional splitting."""

        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            if split_pattern:
                parts = [segment.strip() for segment in re.split(split_pattern, value) if segment.strip()]
                return parts
            trimmed = value.strip()
            return [trimmed] if trimmed else []
        if value is None:
            return []
        warnings.append(
            self._task_graph_warning(
                "state.coerced_field",
                f"Coerced {field} into list form.",
                task_id=task_id,
                detail={"value": value},
            )
        )
        return [str(value)]

    def _coerce_optional_int(
        self,
        value: Any,
        *,
        field: str,
        task_id: str,
        warnings: list[dict[str, Any]],
    ) -> int | None:
        """Coerce ``value`` into a non-negative integer when possible."""

        if value is None:
            return None
        try:
            integer = int(value)
        except (TypeError, ValueError):
            warnings.append(
                self._task_graph_warning(
                    "state.integer_cast_failed",
                    f"Could not parse {field} as integer.",
                    task_id=task_id,
                    detail={"value": value},
                )
            )
            return None
        if integer < 0:
            warnings.append(
                self._task_graph_warning(
                    "state.integer_negative",
                    f"{field} must be non-negative.",
                    task_id=task_id,
                    detail={"value": value},
                )
            )
            return None
        return integer

    def _coerce_optional_text(
        self,
        value: Any,
        *,
        field: str,
        task_id: str,
        warnings: list[dict[str, Any]],
    ) -> str | None:
        """Return trimmed text or ``None`` if unavailable."""

        if value is None:
            return None
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed or None
        try:
            text = str(value).strip()
        except Exception:  # pragma: no cover - defensive
            warnings.append(
                self._task_graph_warning(
                    "state.text_cast_failed",
                    f"Could not cast {field} to text.",
                    task_id=task_id,
                )
            )
            return None
        if not text:
            return None
        warnings.append(
            self._task_graph_warning(
                "state.coerced_text",
                f"Coerced {field} into string form.",
                task_id=task_id,
                detail={"value": value},
            )
        )
        return text

    def _coerce_socratic_checks(
        self,
        value: Any,
        *,
        task_id: str,
        field: str,
        warnings: list[dict[str, Any]],
    ) -> list[str]:
        """Normalise Socratic self-check prompts into strings."""

        if isinstance(value, Mapping):
            collected: list[str] = []
            for key, item in value.items():
                prefix = str(key).strip()
                nested = self._coerce_socratic_checks(
                    item,
                    task_id=task_id,
                    field=f"{field}.{prefix}" if prefix else field,
                    warnings=warnings,
                )
                for prompt in nested:
                    if prefix and not prompt.lower().startswith(prefix.lower()):
                        collected.append(f"{prefix}: {prompt}")
                    else:
                        collected.append(prompt)
            return collected
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            flattened: list[str] = []
            for item in value:
                flattened.extend(
                    self._coerce_socratic_checks(
                        item,
                        task_id=task_id,
                        field=field,
                        warnings=warnings,
                    )
                )
            return flattened
        if isinstance(value, str):
            parts = [segment.strip() for segment in re.split(r"\n|;|\|", value)]
            return [segment for segment in parts if segment]
        if value is None:
            return []
        coerced = str(value).strip()
        if coerced:
            warnings.append(
                self._task_graph_warning(
                    "state.coerced_socratic",
                    "Coerced Socratic check into string form.",
                    task_id=task_id,
                    detail={"value": value},
                )
            )
            return [coerced]
        return []

    def _coerce_dependency_overview(
        self,
        value: Any,
        *,
        warnings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Normalise dependency overview metadata."""

        if value is None:
            return []
        items: Iterable[Any]
        if isinstance(value, Mapping):
            items = [value]
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            items = value
        else:
            warnings.append(
                self._task_graph_warning(
                    "state.dependency_overview_invalid",
                    "Dependency overview must be a mapping or sequence.",
                    detail={"value": value},
                )
            )
            return []
        overview: list[dict[str, Any]] = []
        for entry in items:
            if not isinstance(entry, Mapping):
                warnings.append(
                    self._task_graph_warning(
                        "state.dependency_overview_entry_invalid",
                        "Dependency overview entries must be mappings.",
                        detail={"entry": entry},
                    )
                )
                continue
            task_id = entry.get("task") or entry.get("id")
            sanitized: dict[str, Any] = {}
            if task_id is not None:
                sanitized["task"] = str(task_id)
            depends_on = self._coerce_general_sequence(entry.get("depends_on"))
            if depends_on:
                sanitized["depends_on"] = depends_on
            depth_value = entry.get("depth")
            if depth_value is None:
                depth_value = entry.get("dependency_depth")
            depth = None
            if depth_value is not None:
                depth = self._coerce_optional_int(
                    depth_value,
                    field="dependency_overview.depth",
                    task_id=str(task_id or "overview"),
                    warnings=warnings,
                )
            if depth is not None:
                sanitized["depth"] = depth
            rationale = entry.get("rationale")
            if rationale is None:
                rationale = entry.get("dependency_rationale")
            rationale_text = None
            if rationale is not None:
                rationale_text = self._coerce_optional_text(
                    rationale,
                    field="dependency_overview.rationale",
                    task_id=str(task_id or "overview"),
                    warnings=warnings,
                )
            if rationale_text:
                sanitized["rationale"] = rationale_text
            if sanitized:
                overview.append(sanitized)
        return overview

    def _task_graph_warning(
        self,
        code: str,
        message: str,
        *,
        task_id: str | None = None,
        detail: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return a structured warning payload for task graph normalisation."""

        payload: dict[str, Any] = {"code": code, "message": message}
        if task_id is not None:
            payload["task_id"] = task_id
        if detail is not None:
            payload["detail"] = dict(detail)
        return payload

    def _extract_planner_top_level(self, task_graph: Any) -> dict[str, Any]:
        """Capture top-level planner telemetry fields prior to normalisation."""

        payload: Mapping[str, Any] | None = None
        if isinstance(task_graph, TaskGraph):
            payload = task_graph.to_payload()
        elif isinstance(task_graph, Mapping):
            payload = task_graph

        if payload is None:
            return {}

        snapshot: dict[str, Any] = {}
        objectives = self._coerce_general_sequence(payload.get("objectives"))
        if objectives:
            snapshot["objectives"] = objectives
        exit_criteria = self._coerce_general_sequence(payload.get("exit_criteria"))
        if exit_criteria:
            snapshot["exit_criteria"] = exit_criteria
        explanation = payload.get("explanation")
        if isinstance(explanation, str) and explanation.strip():
            snapshot["explanation"] = explanation.strip()
        return snapshot

    def _planner_telemetry_snapshot(
        self, normalized: Mapping[str, Any], top_level: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Summarise planner telemetry for downstream consumers."""

        tasks_snapshot: list[dict[str, Any]] = []
        for task in normalized.get("tasks", []):
            if not isinstance(task, Mapping):
                continue
            socratic_checks = task.get("socratic_checks")
            if isinstance(socratic_checks, Sequence) and not isinstance(
                socratic_checks, (str, bytes)
            ):
                socratic_list = [
                    str(item).strip() for item in socratic_checks if str(item).strip()
                ]
            else:
                socratic_list = []
            tasks_snapshot.append(
                {
                    "id": str(task.get("id")),
                    "objectives": list(task.get("sub_questions", [])),
                    "tool_affinity": dict(task.get("affinity", {})),
                    "exit_criteria": list(task.get("criteria", [])),
                    "explanation": task.get("explanation"),
                    "dependency_depth": task.get("dependency_depth"),
                    "dependency_rationale": task.get("dependency_rationale"),
                    "socratic_checks": socratic_list,
                }
            )

        telemetry: dict[str, Any] = {
            "tasks": tasks_snapshot,
            "objectives": list(top_level.get("objectives", [])),
            "exit_criteria": list(top_level.get("exit_criteria", [])),
        }
        explanation = top_level.get("explanation")
        if explanation:
            telemetry["explanation"] = explanation
        metadata = normalized.get("metadata")
        if isinstance(metadata, Mapping):
            dependency_overview = metadata.get("dependency_overview")
            if isinstance(dependency_overview, Sequence) and not isinstance(
                dependency_overview, (str, bytes)
            ):
                telemetry["dependency_overview"] = list(dependency_overview)
        return telemetry

    def _coerce_general_sequence(self, value: Any) -> list[str]:
        """Coerce arbitrary payloads into a list of trimmed strings."""

        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            parts = [segment.strip() for segment in re.split(r",|;|/|\n", value)]
            return [segment for segment in parts if segment]
        return []

    # ------------------------------------------------------------------
    # Coalition management utilities
    # ------------------------------------------------------------------

    def add_coalition(self, name: str, members: list[str]) -> None:
        """Register a coalition of agents.

        Args:
            name: Name of the coalition
            members: Agent names that belong to the coalition
        """
        self.coalitions[name] = members

    def remove_coalition(self, name: str) -> None:
        """Remove a coalition if it exists."""
        self.coalitions.pop(name, None)

    def get_coalition_members(self, name: str) -> list[str]:
        """Return members of a coalition."""
        return self.coalitions.get(name, [])

    def get_messages(
        self,
        *,
        recipient: Optional[str] = None,
        coalition: Optional[str] = None,
        protocol: MessageProtocol | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve messages for a specific recipient or coalition."""
        with self._lock:
            messages = list(self.messages)
        if recipient is not None:
            messages = [m for m in messages if m.get("to") in (None, recipient)]
        if coalition is not None:
            members = self.coalitions.get(coalition, [])
            messages = [m for m in messages if m.get("from") in members]
        if protocol is not None:
            messages = [m for m in messages if m.get("protocol") == protocol.value]
        return messages

    def __getstate__(self) -> dict[str, Any]:
        """Drop non-serializable members before pickling."""

        state: dict[str, Any] = self.model_dump(mode="python")
        state.pop("_lock", None)
        state.pop("__pydantic_private__", None)
        state.pop("_abc_impl", None)
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Restore serialization-safe state and recreate the lock."""

        cleaned_state = {
            key: value
            for key, value in state.items()
            if key not in {"_lock", "__pydantic_private__", "_abc_impl"}
        }
        restored = type(self).model_validate(cleaned_state)

        self.__dict__.clear()
        self.__dict__.update(restored.__dict__)

        private_state = getattr(restored, "__pydantic_private__", None)
        if private_state is not None:
            object.__setattr__(self, "__pydantic_private__", private_state)

        fields_set = getattr(restored, "__pydantic_fields_set__", None)
        if fields_set is not None:
            object.__setattr__(self, "__pydantic_fields_set__", fields_set)

        self._ensure_lock()

    def synthesize(self) -> QueryResponse:
        """Create final response from state."""
        auditor = AnswerAuditor(self)
        outcome = auditor.review()

        self.claim_audits = list(outcome.claim_audits)
        self.claims = list(outcome.reasoning)
        if isinstance(self.results, Mapping):
            self.results.setdefault("final_answer", outcome.answer)
            self.results["final_answer"] = outcome.answer

        existing_sources = {str(src.get("source_id")) for src in self.sources if isinstance(src, Mapping)}
        for source in outcome.additional_sources:
            source_id = str(source.get("source_id") or "")
            if source_id and source_id in existing_sources:
                continue
            self.sources.append(dict(source))
            if source_id:
                existing_sources.add(source_id)

        metrics = dict(self.metadata)
        audit_metrics_existing = metrics.get("answer_audit")
        merged_audit_metrics: dict[str, Any]
        if isinstance(audit_metrics_existing, Mapping):
            merged_audit_metrics = dict(audit_metrics_existing)
        else:
            merged_audit_metrics = {}
        merged_audit_metrics.update(outcome.metrics)
        metrics["answer_audit"] = merged_audit_metrics

        graph_summary = SearchContext.get_instance().get_graph_summary()
        if graph_summary:
            knowledge_graph_meta: dict[str, Any] = {}
            existing = metrics.get("knowledge_graph")
            if isinstance(existing, Mapping):
                knowledge_graph_meta.update(existing)
            knowledge_graph_meta["summary"] = graph_summary
            entity_count = int(graph_summary.get("entity_count", 0) or 0)
            relation_count = int(graph_summary.get("relation_count", 0) or 0)
            has_graph = bool(entity_count or relation_count)
            exports_meta = graph_summary.get("exports") if isinstance(graph_summary, Mapping) else None
            if isinstance(exports_meta, Mapping):
                knowledge_graph_meta["exports"] = {
                    "graphml": bool(exports_meta.get("graphml")),
                    "graph_json": bool(exports_meta.get("graph_json")),
                }
            elif has_graph:
                knowledge_graph_meta["exports"] = {"graphml": True, "graph_json": True}
            metrics["knowledge_graph"] = knowledge_graph_meta

        return QueryResponse(
            query=self.query,
            answer=outcome.answer,
            citations=self.sources,
            reasoning=self.claims,
            metrics=metrics,
            warnings=list(outcome.warnings),
            claim_audits=self.claim_audits,
            task_graph=self.task_graph if self.task_graph.get("tasks") else None,
            react_traces=list(self.react_traces),
        )

    def get_dialectical_structure(self) -> dict[str, Any]:
        """Extract thesis, antithesis, verification, and synthesis claims."""
        structure: dict[str, Any] = {
            "thesis": None,
            "antithesis": [],
            "verification": [],
            "synthesis": None,
        }

        # Extract claims by type
        for claim in self.claims:
            claim_type = claim.get("type")
            if claim_type == "thesis":
                structure["thesis"] = claim
            elif claim_type == "antithesis":
                structure["antithesis"].append(claim)
            elif claim_type == "verification":
                structure["verification"].append(claim)
            elif claim_type == "synthesis":
                structure["synthesis"] = claim

        return structure

    def prune_context(
        self,
        max_claims: int = 50,
        max_sources: int = 20,
        max_messages: int = 50,
        max_feedback: int = 50,
    ) -> None:
        """Prune stored context to keep the state manageable.

        This method removes the oldest claims and sources when their count
        exceeds the provided limits. A summary of the number of items pruned
        is stored under ``metadata['pruned']``.

        Args:
            max_claims: Maximum number of claims to keep.
            max_sources: Maximum number of sources to keep.
        """

        with self._lock:
            pruned = {"claims": 0, "sources": 0, "messages": 0, "feedback": 0}

            if len(self.claims) > max_claims:
                excess = len(self.claims) - max_claims
                del self.claims[0:excess]
                pruned["claims"] = excess

            if len(self.sources) > max_sources:
                excess = len(self.sources) - max_sources
                del self.sources[0:excess]
                pruned["sources"] = excess

            if len(self.messages) > max_messages:
                excess = len(self.messages) - max_messages
                del self.messages[0:excess]
                pruned["messages"] = excess

            if len(self.feedback_events) > max_feedback:
                excess = len(self.feedback_events) - max_feedback
                del self.feedback_events[0:excess]
                pruned["feedback"] = excess

            if any(pruned.values()):
                self.metadata.setdefault("pruned", []).append(pruned)

    def _ensure_lock(self) -> None:
        """Guarantee the internal lock exists after serialization events."""
        lock = getattr(self, "_lock", None)
        if not isinstance(lock, LOCK_TYPE):
            object.__setattr__(self, "_lock", RLock())
