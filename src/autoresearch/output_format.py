"""Adaptive output formatting for CLI and automation contexts."""

from __future__ import annotations

import json
import re
import sys
import string
import unicodedata
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence
from pydantic import BaseModel, ValidationError
from .models import QueryResponse
from .errors import ValidationError as AutoresearchValidationError
from .config import ConfigLoader
from .logging_utils import get_logger
from .storage import StorageManager

log = get_logger(__name__)


class OutputDepth(IntEnum):
    """Enumerate output detail levels for deterministic rendering."""

    TLDR = 0
    CONCISE = 1
    STANDARD = 2
    TRACE = 3

    @property
    def label(self) -> str:
        """Human-friendly label."""

        return {
            OutputDepth.TLDR: "TL;DR",
            OutputDepth.CONCISE: "Concise",
            OutputDepth.STANDARD: "Standard",
            OutputDepth.TRACE: "Trace",
        }[self]

    @property
    def description(self) -> str:
        """Describe the scope of this depth level."""

        return {
            OutputDepth.TLDR: "Highlight the TL;DR, answer, and top citations only.",
            OutputDepth.CONCISE: (
                "Add key findings and a short citation roll-up for quick reviews."
            ),
            OutputDepth.STANDARD: (
                "Include claim tables, expanded citations, and summary reasoning."
            ),
            OutputDepth.TRACE: (
                "Expose the full reasoning trace, complete audits, and raw payloads."
            ),
        }[self]


@dataclass(frozen=True)
class DepthPlan:
    """Plan describing which sections to include for a depth selection."""

    level: OutputDepth
    include_tldr: bool
    include_key_findings: bool
    key_findings_limit: Optional[int]
    include_citations: bool
    citation_limit: Optional[int]
    include_claims: bool
    claim_limit: Optional[int]
    include_reasoning: bool
    reasoning_limit: Optional[int]
    include_metrics: bool
    include_raw: bool
    include_task_graph: bool
    task_graph_limit: Optional[int]
    include_react_traces: bool
    react_trace_limit: Optional[int]
    include_knowledge_graph: bool
    knowledge_graph_contradiction_limit: Optional[int]
    knowledge_graph_path_limit: Optional[int]
    include_graph_exports: bool


@dataclass
class DepthPayload:
    """Structured payload returned by depth-aware render planning."""

    depth: OutputDepth
    tldr: str
    answer: str
    key_findings: list[str]
    citations: list[Any]
    claim_audits: list[dict[str, Any]]
    reasoning: list[str]
    metrics: dict[str, Any]
    raw_response: Optional[dict[str, Any]]
    task_graph: Optional[dict[str, Any]]
    react_traces: list[dict[str, Any]]
    knowledge_graph: Optional[dict[str, Any]]
    graph_exports: dict[str, bool]
    graph_export_payloads: dict[str, str]
    sections: dict[str, bool]
    warnings: list[dict[str, Any]] = field(default_factory=list)
    notes: dict[str, str] = field(default_factory=dict)
    state_id: str | None = None


_DEPTH_ALIASES: Dict[str, OutputDepth] = {
    "tldr": OutputDepth.TLDR,
    "summary": OutputDepth.TLDR,
    "0": OutputDepth.TLDR,
    "concise": OutputDepth.CONCISE,
    "quick": OutputDepth.CONCISE,
    "1": OutputDepth.CONCISE,
    "standard": OutputDepth.STANDARD,
    "default": OutputDepth.STANDARD,
    "claims": OutputDepth.STANDARD,
    "2": OutputDepth.STANDARD,
    "trace": OutputDepth.TRACE,
    "full": OutputDepth.TRACE,
    "deep": OutputDepth.TRACE,
    "debug": OutputDepth.TRACE,
    "3": OutputDepth.TRACE,
}


_DEPTH_PLANS: Dict[OutputDepth, DepthPlan] = {
    OutputDepth.TLDR: DepthPlan(
        level=OutputDepth.TLDR,
        include_tldr=True,
        include_key_findings=False,
        key_findings_limit=None,
        include_citations=True,
        citation_limit=2,
        include_claims=False,
        claim_limit=None,
        include_reasoning=False,
        reasoning_limit=None,
        include_metrics=False,
        include_raw=False,
        include_task_graph=False,
        task_graph_limit=None,
        include_react_traces=False,
        react_trace_limit=None,
        include_knowledge_graph=True,
        knowledge_graph_contradiction_limit=1,
        knowledge_graph_path_limit=1,
        include_graph_exports=False,
    ),
    OutputDepth.CONCISE: DepthPlan(
        level=OutputDepth.CONCISE,
        include_tldr=True,
        include_key_findings=True,
        key_findings_limit=3,
        include_citations=True,
        citation_limit=3,
        include_claims=False,
        claim_limit=None,
        include_reasoning=False,
        reasoning_limit=None,
        include_metrics=True,
        include_raw=False,
        include_task_graph=False,
        task_graph_limit=None,
        include_react_traces=False,
        react_trace_limit=None,
        include_knowledge_graph=True,
        knowledge_graph_contradiction_limit=2,
        knowledge_graph_path_limit=2,
        include_graph_exports=False,
    ),
    OutputDepth.STANDARD: DepthPlan(
        level=OutputDepth.STANDARD,
        include_tldr=True,
        include_key_findings=True,
        key_findings_limit=None,
        include_citations=True,
        citation_limit=None,
        include_claims=True,
        claim_limit=5,
        include_reasoning=True,
        reasoning_limit=8,
        include_metrics=True,
        include_raw=False,
        include_task_graph=True,
        task_graph_limit=3,
        include_react_traces=False,
        react_trace_limit=None,
        include_knowledge_graph=True,
        knowledge_graph_contradiction_limit=3,
        knowledge_graph_path_limit=3,
        include_graph_exports=True,
    ),
    OutputDepth.TRACE: DepthPlan(
        level=OutputDepth.TRACE,
        include_tldr=True,
        include_key_findings=True,
        key_findings_limit=None,
        include_citations=True,
        citation_limit=None,
        include_claims=True,
        claim_limit=None,
        include_reasoning=True,
        reasoning_limit=None,
        include_metrics=True,
        include_raw=True,
        include_task_graph=True,
        task_graph_limit=None,
        include_react_traces=True,
        react_trace_limit=None,
        include_knowledge_graph=True,
        knowledge_graph_contradiction_limit=None,
        knowledge_graph_path_limit=None,
        include_graph_exports=True,
    ),
}


_STATUS_BADGES: Dict[str, tuple[str, str]] = {
    "supported": ("🟢", "Supported"),
    "unsupported": ("🔴", "Unsupported"),
    "needs_review": ("🟡", "Needs review"),
}


def get_depth_aliases() -> Dict[str, OutputDepth]:
    """Return a copy of the registered depth aliases."""

    return dict(_DEPTH_ALIASES)


def normalize_depth(depth: Any) -> OutputDepth:
    """Normalise depth selection into an :class:`OutputDepth`."""

    if depth is None:
        return OutputDepth.STANDARD
    if isinstance(depth, OutputDepth):
        return depth
    if isinstance(depth, str):
        key = depth.strip().lower()
        if key in _DEPTH_ALIASES:
            return _DEPTH_ALIASES[key]
        msg = ", ".join(sorted({alias for alias in _DEPTH_ALIASES if alias.isalpha()}))
        raise ValueError(f"Unknown depth '{depth}'. Valid options: {msg} or 0-3.")
    if isinstance(depth, int):
        try:
            return OutputDepth(depth)
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError("Depth integers must be between 0 and 3.") from exc
    raise ValueError(f"Unsupported depth type: {type(depth)!r}")


def describe_depth_levels() -> Dict[OutputDepth, str]:
    """Provide descriptions for each depth level."""

    return {level: level.description for level in OutputDepth}


def describe_depth_features() -> Dict[OutputDepth, Dict[str, bool]]:
    """Summarise which headline sections are exposed at each depth."""

    features: Dict[OutputDepth, Dict[str, bool]] = {}
    for depth, plan in _DEPTH_PLANS.items():
        features[depth] = {
            "tldr": plan.include_tldr,
            "key_findings": plan.include_key_findings,
            "claim_audits": plan.include_claims,
            "full_trace": plan.include_reasoning and plan.include_react_traces,
            "knowledge_graph": plan.include_knowledge_graph,
            "graph_exports": plan.include_graph_exports,
        }
    return features


_SECTION_LABELS: Dict[str, str] = {
    "tldr": "TL;DR",
    "key_findings": "Key findings",
    "citations": "Citations",
    "claim_audits": "Claim audits",
    "reasoning": "Reasoning trace",
    "metrics": "Metrics",
    "raw_response": "Raw response",
    "task_graph": "Task graph",
    "react_traces": "ReAct traces",
    "knowledge_graph": "Knowledge graph",
    "knowledge_graph_contradictions": "Knowledge graph contradictions",
    "knowledge_graph_paths": "Knowledge graph paths",
    "graph_exports": "Graph exports",
}


def _canonical_graph_format(name: Any) -> str | None:
    """Return the canonical identifier for a graph export format."""

    if name is None:
        return None
    token = str(name).strip().lower()
    if not token:
        return None
    token = token.replace("-", "_")
    if token in {"graphml", "graph_json"}:
        return token
    if token in {"graphjson"}:
        return "graph_json"
    return None


def _fetch_graph_exports(formats: Iterable[str]) -> dict[str, str]:
    """Return serialized graph exports for the requested ``formats``."""

    requested = {
        canonical
        for canonical in (_canonical_graph_format(fmt) for fmt in formats)
        if canonical
    }
    if not requested:
        return {}

    try:  # pragma: no cover - import guards optional extras during docs builds
        from .knowledge import SessionGraphPipeline
    except Exception as exc:  # pragma: no cover - dependency may be optional
        log.debug("SessionGraphPipeline unavailable for graph exports: %s", exc)
        return {}

    pipeline = SessionGraphPipeline()
    try:
        artifacts = pipeline.export_artifacts()
    except Exception as exc:  # pragma: no cover - downstream storage errors
        log.debug("Graph export retrieval failed: %s", exc)
        return {}

    payloads: dict[str, str] = {}
    for fmt in requested:
        raw = artifacts.get(fmt) or artifacts.get(fmt.replace("_", "-"))
        if isinstance(raw, str) and raw.strip():
            payloads[fmt] = raw
    return payloads


def _hidden_message(section: str, plan: DepthPlan) -> str:
    """Return a consistent message for hidden sections."""

    next_level = OutputDepth(min(plan.level + 1, OutputDepth.TRACE))
    label = _SECTION_LABELS.get(section, section.replace("_", " ").title())
    if next_level == plan.level:
        return f"{label} are available only at the {next_level.label} depth."
    return (
        f"{label} are hidden at the {plan.level.label} depth. "
        f"Increase depth to {next_level.label} to view them."
    )


def _truncation_message(section: str, shown: int, total: int, depth: OutputDepth) -> str:
    """Return a message describing truncated sections."""

    label = _SECTION_LABELS.get(section, section.replace("_", " ").title())
    return (
        f"Showing the first {shown} of {total} {label.lower()}. "
        f"Use the {OutputDepth.TRACE.label} depth for the complete view."
        if depth != OutputDepth.TRACE
        else f"Showing {shown} of {total} {label.lower()}."
    )


def _stringify_reasoning(reasoning: Iterable[Any]) -> List[str]:
    """Normalise reasoning steps into display strings."""

    steps: List[str] = []
    for step in reasoning:
        if isinstance(step, str):
            if step == "":
                continue
            steps.append(step)
            continue
        if isinstance(step, Mapping):
            visibility = step.get("visibility")
            if isinstance(visibility, Mapping) and visibility.get("reasoning") is False:
                continue
            for key in ("hedged_content", "summary", "content", "text", "message"):
                value = step.get(key)
                if isinstance(value, str):
                    if value == "":
                        continue
                    steps.append(value)
                    break
            else:
                steps.append(json.dumps(step, ensure_ascii=False))
            continue
        steps.append(str(step))
    return steps


def _generate_key_findings(response: QueryResponse) -> List[str]:
    """Derive key findings from reasoning or the synthesized answer."""

    findings: List[str] = []
    for step in response.reasoning:
        if isinstance(step, Mapping):
            visibility = step.get("visibility")
            if isinstance(visibility, Mapping) and visibility.get("key_findings") is False:
                continue
            status_value = step.get("audit_status")
            if not isinstance(status_value, str):
                status_value = step.get("audit", {}).get("status")
            status_text = str(status_value or "").lower()
            if status_text == "unsupported":
                continue
            for key in ("hedged_content", "summary", "content", "text", "message"):
                value = step.get(key)
                if isinstance(value, str):
                    if value == "":
                        continue
                    findings.append(value)
                    break
            continue
        if isinstance(step, str) and step != "":
            findings.append(step)
    if not findings:
        answer_lines = [
            line
            for line in response.answer.splitlines()
            if line
            and not line.lstrip().startswith("⚠️")
            and "unsupported claims remain" not in line.lower()
            and "needs review" not in line.lower()
        ]
        findings.extend(answer_lines[:3])
    return findings


def _generate_tldr(response: QueryResponse, max_length: int = 240) -> str:
    """Produce a TL;DR style summary from the answer."""

    answer = (response.answer or "").strip()
    if not answer:
        return "No answer generated."
    match = re.search(r"(?<!\w)([.!?])", answer)
    if match:
        cutoff = match.end()
        snippet = answer[:cutoff]
    else:
        snippet = answer[: max_length + 1]
    if len(snippet) > max_length:
        snippet = snippet[:max_length].rstrip() + "…"
    return snippet


def _limit_items(sequence: Iterable[Any], limit: Optional[int]) -> tuple[list[Any], Optional[int]]:
    """Limit a sequence and report the original length when truncated."""

    values = list(sequence)
    if limit is None:
        return values, None
    limited = values[:limit]
    if len(values) > limit:
        return limited, len(values)
    return limited, None


def build_depth_payload(
    response: QueryResponse,
    depth: Any = None,
    *,
    graph_preview_enabled: bool | None = None,
    graph_exports_enabled: bool | None = None,
    graph_export_formats: Iterable[str] | None = None,
    prefetch_graph_exports: bool | None = None,
) -> DepthPayload:
    """Construct a depth-aware payload for formatting and UI layers."""

    depth_level = normalize_depth(depth)
    plan = _DEPTH_PLANS[depth_level]
    notes: dict[str, str] = {}

    try:
        cfg = ConfigLoader().config
        preferences = (
            dict(getattr(cfg, "user_preferences", {}))
            if hasattr(cfg, "user_preferences")
            else {}
        )
    except Exception:  # pragma: no cover - configuration loading failures are logged elsewhere
        preferences = {}

    preview_allowed = (
        graph_preview_enabled
        if graph_preview_enabled is not None
        else bool(preferences.get("graph_preview_enabled", True))
    )
    exports_allowed = (
        graph_exports_enabled
        if graph_exports_enabled is not None
        else bool(preferences.get("graph_exports_enabled", True))
    )
    prefetch_allowed = (
        prefetch_graph_exports
        if prefetch_graph_exports is not None
        else bool(preferences.get("prefetch_graph_exports", False))
    )

    configured_formats: list[str] = []
    pref_formats = preferences.get("graph_export_formats")
    if isinstance(pref_formats, Sequence) and not isinstance(pref_formats, (str, bytes)):
        seen_pref: set[str] = set()
        for value in pref_formats:
            canonical = _canonical_graph_format(value)
            if canonical and canonical not in seen_pref:
                seen_pref.add(canonical)
        configured_formats = list(seen_pref)

    explicit_formats: list[str] = []
    if graph_export_formats is not None:
        seen_explicit: set[str] = set()
        for value in graph_export_formats:
            canonical = _canonical_graph_format(value)
            if canonical and canonical not in seen_explicit:
                seen_explicit.add(canonical)
        explicit_formats = list(seen_explicit)

    if plan.include_tldr:
        tldr = _generate_tldr(response)
    else:
        tldr = ""
        notes["tldr"] = _hidden_message("tldr", plan)

    answer = response.answer

    if plan.include_key_findings:
        findings_all = _generate_key_findings(response)
        findings, truncated = _limit_items(findings_all, plan.key_findings_limit)
        if truncated is not None:
            notes["key_findings"] = _truncation_message(
                "key_findings", len(findings), truncated, depth_level
            )
    else:
        findings = []
        notes["key_findings"] = _hidden_message("key_findings", plan)

    if plan.include_citations:
        citations, truncated = _limit_items(response.citations, plan.citation_limit)
        if truncated is not None:
            notes["citations"] = _truncation_message(
                "citations", len(citations), truncated, depth_level
            )
    else:
        citations = []
        notes["citations"] = _hidden_message("citations", plan)

    if plan.include_claims:
        claim_audits, truncated = _limit_items(response.claim_audits, plan.claim_limit)
        if truncated is not None:
            notes["claim_audits"] = _truncation_message(
                "claim_audits", len(claim_audits), truncated, depth_level
            )
    else:
        claim_audits = []
        notes["claim_audits"] = _hidden_message("claim_audits", plan)

    if plan.include_reasoning:
        reasoning_all = _stringify_reasoning(response.reasoning)
        reasoning, truncated = _limit_items(reasoning_all, plan.reasoning_limit)
        if truncated is not None:
            notes["reasoning"] = _truncation_message(
                "reasoning", len(reasoning), truncated, depth_level
            )
    else:
        reasoning = []
        notes["reasoning"] = _hidden_message("reasoning", plan)

    if plan.include_metrics:
        metrics = dict(response.metrics)
    else:
        metrics = {}
        notes["metrics"] = _hidden_message("metrics", plan)

    def _truncate_claim(text: str, limit: int = 80) -> str:
        cleaned = " ".join(text.split())
        if len(cleaned) <= limit:
            return cleaned
        return cleaned[: limit - 1].rstrip() + "…"

    def _claim_labels(ids: Iterable[Any]) -> list[str]:
        labels: list[str] = []
        for claim_id in ids:
            cid = str(claim_id)
            label = cid
            for step in response.reasoning:
                if isinstance(step, Mapping) and str(step.get("id")) == cid:
                    for key in ("hedged_content", "content", "summary", "text", "message"):
                        value = step.get(key)
                        if isinstance(value, str) and value.strip():
                            label = _truncate_claim(value)
                            break
                    break
            labels.append(label)
        return labels

    warning_lookup: dict[str, Mapping[str, Any]] = {}
    warnings_payload: list[dict[str, Any]] = []
    for entry in response.warnings:
        if isinstance(entry, Mapping):
            code = str(entry.get("code") or "")
            if code:
                warning_lookup[code] = entry
            warnings_payload.append(dict(entry))
        else:
            warnings_payload.append({"message": str(entry)})

    audit_snapshot = metrics.get("answer_audit") if isinstance(metrics, Mapping) else None

    def _warning_claim_ids(entry: Mapping[str, Any]) -> list[str]:
        ids = [
            str(claim_id)
            for claim_id in entry.get("claim_ids", [])
            if claim_id is not None and str(claim_id)
        ]
        if ids:
            return ids
        claims_payload = entry.get("claims", [])
        extracted: list[str] = []
        if isinstance(claims_payload, Sequence) and not isinstance(
            claims_payload, (str, bytes, bytearray)
        ):
            for claim in claims_payload:
                if isinstance(claim, Mapping):
                    claim_id = claim.get("id")
                    if claim_id is not None and str(claim_id):
                        extracted.append(str(claim_id))
        return extracted

    def _warning_labels(entry: Mapping[str, Any], fallback_ids: list[str]) -> list[str]:
        labels: list[str] = []
        claims_payload = entry.get("claims", [])
        if isinstance(claims_payload, Sequence) and not isinstance(
            claims_payload, (str, bytes, bytearray)
        ):
            for claim in claims_payload:
                if isinstance(claim, Mapping):
                    label = claim.get("label")
                    if isinstance(label, str) and label.strip():
                        labels.append(label)
        if labels:
            return labels
        return _claim_labels(fallback_ids)

    unsupported_warning = warning_lookup.get("answer_audit.unsupported_claims")
    needs_review_warning = warning_lookup.get("answer_audit.needs_review_claims")

    if unsupported_warning is None and isinstance(audit_snapshot, Mapping):
        unsupported_ids_fallback = [
            str(claim_id)
            for claim_id in audit_snapshot.get("unsupported_claims", [])
            if claim_id is not None and str(claim_id)
        ]
    else:
        unsupported_ids_fallback = []

    if needs_review_warning is None and isinstance(audit_snapshot, Mapping):
        needs_review_ids_fallback = [
            str(claim_id)
            for claim_id in audit_snapshot.get("needs_review_claims", [])
            if claim_id is not None and str(claim_id)
        ]
    else:
        needs_review_ids_fallback = []

    if unsupported_warning is not None:
        unsupported_ids = _warning_claim_ids(unsupported_warning)
        if not unsupported_ids:
            unsupported_ids = unsupported_ids_fallback
        if unsupported_ids:
            labels = _warning_labels(unsupported_warning, unsupported_ids)
            caution = "Unsupported claims were removed from the summary: " + ", ".join(labels)
            key_note = notes.get("key_findings")
            notes["key_findings"] = f"{key_note} {caution}".strip() if key_note else caution
            claim_note = notes.get("claim_audits")
            claim_warning = "Unsupported claims remain after retries: " + ", ".join(labels)
            notes["claim_audits"] = (
                f"{claim_note} {claim_warning}".strip() if claim_note else claim_warning
            )
            tldr_note = notes.get("tldr")
            notes["tldr"] = f"{tldr_note} {caution}".strip() if tldr_note else caution
    elif needs_review_warning is not None or needs_review_ids_fallback:
        warning_entry = needs_review_warning
        needs_review_ids = (
            _warning_claim_ids(warning_entry)
            if warning_entry is not None
            else needs_review_ids_fallback
        )
        if not needs_review_ids:
            needs_review_ids = needs_review_ids_fallback
        if needs_review_ids:
            labels = _warning_labels(warning_entry or {}, needs_review_ids)
            review_note = "Some claims still require review: " + ", ".join(labels)
            key_note = notes.get("key_findings")
            notes["key_findings"] = (
                f"{key_note} {review_note}".strip() if key_note else review_note
            )
            claim_note = notes.get("claim_audits")
            notes["claim_audits"] = (
                f"{claim_note} {review_note}".strip() if claim_note else review_note
            )

    knowledge_graph_payload: Optional[dict[str, Any]] = None
    graph_exports_payload: dict[str, bool] = {}
    graph_export_payloads: dict[str, str] = {}
    if plan.include_knowledge_graph:
        if not preview_allowed:
            notes["knowledge_graph"] = "Knowledge graph preview disabled by configuration."
            if plan.include_graph_exports:
                notes.setdefault(
                    "graph_exports",
                    "Graph exports disabled while knowledge graph preview is off.",
                )
        else:
            knowledge_meta = response.metrics.get("knowledge_graph")
            if isinstance(knowledge_meta, Mapping):
                summary = knowledge_meta.get("summary")
                if isinstance(summary, Mapping) and summary:
                    summary_payload: dict[str, Any] = {}
                    entity_count = summary.get("entity_count")
                    if isinstance(entity_count, (int, float)):
                        summary_payload["entity_count"] = int(entity_count)
                    relation_count = summary.get("relation_count")
                    if isinstance(relation_count, (int, float)):
                        summary_payload["relation_count"] = int(relation_count)
                    contradiction_score = summary.get("contradiction_score")
                    if isinstance(contradiction_score, (int, float)):
                        summary_payload["contradiction_score"] = float(
                            contradiction_score
                        )

                    contradictions_all = summary.get("contradictions") or []
                    if not isinstance(contradictions_all, Sequence) or isinstance(
                        contradictions_all, (str, bytes)
                    ):
                        contradictions_all = []
                    limited_contradictions, truncated_contradictions = _limit_items(
                        contradictions_all, plan.knowledge_graph_contradiction_limit
                    )
                    formatted_contradictions: list[dict[str, Any]] = []
                    for item in limited_contradictions:
                        if isinstance(item, Mapping):
                            formatted_contradictions.append(
                                {
                                    "subject": str(item.get("subject", "")),
                                    "predicate": str(item.get("predicate", "")),
                                    "objects": [str(obj) for obj in item.get("objects", [])],
                                }
                            )
                        else:
                            formatted_contradictions.append({"text": str(item)})
                    if formatted_contradictions:
                        summary_payload["contradictions"] = formatted_contradictions
                    if truncated_contradictions is not None:
                        notes["knowledge_graph_contradictions"] = _truncation_message(
                            "knowledge_graph_contradictions",
                            len(formatted_contradictions),
                            truncated_contradictions,
                            depth_level,
                        )

                    paths_all = summary.get("multi_hop_paths") or []
                    if not isinstance(paths_all, Sequence) or isinstance(
                        paths_all, (str, bytes)
                    ):
                        paths_all = []
                    limited_paths, truncated_paths = _limit_items(
                        paths_all, plan.knowledge_graph_path_limit
                    )
                    formatted_paths: list[list[str]] = []
                    for path in limited_paths:
                        if isinstance(path, Sequence) and not isinstance(
                            path, (str, bytes)
                        ):
                            formatted_paths.append([str(node) for node in path])
                        else:
                            formatted_paths.append([str(path)])
                    if formatted_paths:
                        summary_payload["multi_hop_paths"] = formatted_paths
                    if truncated_paths is not None:
                        notes["knowledge_graph_paths"] = _truncation_message(
                            "knowledge_graph_paths",
                            len(formatted_paths),
                            truncated_paths,
                            depth_level,
                        )

                    timestamp = summary.get("timestamp")
                    if isinstance(timestamp, (int, float)):
                        summary_payload["timestamp"] = float(timestamp)

                    knowledge_graph_payload = summary_payload or None

                    if plan.include_graph_exports:
                        if not exports_allowed:
                            notes.setdefault(
                                "graph_exports",
                                "Graph exports disabled by configuration.",
                            )
                        else:
                            exports_meta = knowledge_meta.get("exports")
                            exports_payload: dict[str, bool] = {}
                            if isinstance(exports_meta, Mapping):
                                for fmt in ("graphml", "graph_json"):
                                    exports_payload[fmt] = bool(exports_meta.get(fmt))
                            elif knowledge_graph_payload:
                                exports_payload = {"graphml": True, "graph_json": True}
                            graph_exports_payload = {
                                fmt: available
                                for fmt, available in exports_payload.items()
                                if available
                            }
            if (
                knowledge_graph_payload is None
                and plan.include_graph_exports
                and exports_allowed
            ):
                graph_exports_payload = {}
    else:
        notes["knowledge_graph"] = _hidden_message("knowledge_graph", plan)
        if plan.include_graph_exports:
            notes["graph_exports"] = _hidden_message("graph_exports", plan)

    available_export_formats = [
        fmt for fmt, available in graph_exports_payload.items() if available
    ]
    fetch_candidates: list[str] = []
    if knowledge_graph_payload and plan.include_graph_exports and exports_allowed:
        if explicit_formats:
            if available_export_formats:
                fetch_candidates = [
                    fmt for fmt in explicit_formats if fmt in available_export_formats
                ]
            else:
                fetch_candidates = list(explicit_formats)
        elif prefetch_allowed:
            fetch_candidates = list(available_export_formats)
            if not fetch_candidates:
                fallback = configured_formats or ["graphml", "graph_json"]
                fetch_candidates = fallback
    if fetch_candidates:
        fetch_candidates = list(dict.fromkeys(fetch_candidates))
        graph_export_payloads = _fetch_graph_exports(fetch_candidates)
        if graph_export_payloads:
            for fmt in graph_export_payloads:
                graph_exports_payload.setdefault(fmt, True)
        else:
            notes.setdefault(
                "graph_exports",
                "Graph exports are not available for this session yet.",
            )

    if plan.include_task_graph:
        graph_payload: Optional[dict[str, Any]] = None
        if response.task_graph:
            if isinstance(response.task_graph, Mapping):
                graph_payload = dict(response.task_graph)
            else:
                graph_payload = {"tasks": list(response.task_graph)}
            tasks_all = graph_payload.get("tasks", [])
            limited_tasks, truncated = _limit_items(tasks_all, plan.task_graph_limit)
            graph_payload["tasks"] = [
                dict(task) if isinstance(task, Mapping) else {"value": task}
                for task in limited_tasks
            ]
            if truncated is not None:
                notes["task_graph"] = _truncation_message(
                    "task_graph", len(limited_tasks), truncated, depth_level
                )
        else:
            graph_payload = None
    else:
        graph_payload = None
        notes["task_graph"] = _hidden_message("task_graph", plan)

    if plan.include_react_traces:
        traces_all = list(response.react_traces)
        react_traces_limited, truncated = _limit_items(
            traces_all, plan.react_trace_limit
        )
        react_traces_payload: list[dict[str, Any]] = []
        for trace in react_traces_limited:
            if isinstance(trace, Mapping):
                react_traces_payload.append(dict(trace))
            else:
                react_traces_payload.append({"value": trace})
        if truncated is not None:
            notes["react_traces"] = _truncation_message(
                "react_traces", len(react_traces_payload), truncated, depth_level
            )
    else:
        react_traces_payload = []
        notes["react_traces"] = _hidden_message("react_traces", plan)

    raw_response = response.model_dump() if plan.include_raw else None
    if raw_response is None:
        notes["raw_response"] = _hidden_message("raw_response", plan)

    sections = {
        "tldr": plan.include_tldr,
        "key_findings": plan.include_key_findings,
        "citations": plan.include_citations,
        "claim_audits": plan.include_claims,
        "reasoning": plan.include_reasoning,
        "metrics": plan.include_metrics,
        "raw_response": plan.include_raw,
        "task_graph": plan.include_task_graph,
        "react_traces": plan.include_react_traces,
        "full_trace": plan.include_reasoning and plan.include_react_traces,
        "knowledge_graph": bool(knowledge_graph_payload) and preview_allowed,
        "graph_exports": bool(graph_exports_payload) and exports_allowed,
    }

    return DepthPayload(
        depth=depth_level,
        tldr=tldr,
        answer=answer,
        key_findings=findings,
        citations=[c for c in citations],
        claim_audits=[dict(a) for a in claim_audits],
        reasoning=reasoning,
        metrics=metrics,
        raw_response=raw_response,
        task_graph=graph_payload,
        react_traces=react_traces_payload,
        knowledge_graph=knowledge_graph_payload,
        graph_exports=graph_exports_payload,
        graph_export_payloads=graph_export_payloads,
        sections=sections,
        warnings=warnings_payload,
        notes=notes,
        state_id=response.state_id,
    )


def _json_safe(value: Any) -> Any:
    """Convert values into JSON-serialisable structures."""

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return [_json_safe(v) for v in value]
    return str(value)


_BLOCK_WHITESPACE = {"\n", "\r", "\t"}


def _indent_block_lines(text: str, indent: str) -> str:
    """Indent ``text`` for Markdown code blocks without losing control bytes."""

    if text == "":
        return indent
    segments = text.splitlines(keepends=True)
    if not segments:
        segments = [""]
    indented: list[str] = []
    for segment in segments:
        if segment:
            indented.append(f"{indent}{segment}")
        else:
            indented.append(indent)
    return "".join(indented)


def _escape_markdown_text(value: str) -> tuple[str, bool]:
    """Escape control characters for safe Markdown rendering."""

    sanitized_chars: list[str] = []
    needs_block = False
    for char in value:
        if char == "\n":
            sanitized_chars.append(char)
            needs_block = True
            continue
        if char == "\r":
            sanitized_chars.append("\\u000d")
            needs_block = True
            continue
        if char == "\t":
            sanitized_chars.append("\\u0009")
            needs_block = True
            continue
        code_point = ord(char)
        category = unicodedata.category(char)
        if category in {"Cc", "Cf"} or code_point == 0x7F:
            sanitized_chars.append(f"\\u{code_point:04x}")
            needs_block = True
        else:
            sanitized_chars.append(char)
    sanitized = "".join(sanitized_chars)
    if sanitized and not sanitized.strip():
        sanitized = "".join(f"\\u{ord(char):04x}" for char in value)
        needs_block = True
    return sanitized, needs_block


def _prepare_markdown_text(
    value: Any, *, block_multiline: bool = False
) -> tuple[str, bool, bool]:
    """Return sanitized text, block flag, and placeholder marker."""

    if value is None:
        return "—", False, True
    text = str(value)
    if text == "":
        return "—", False, True
    sanitized, needs_block = _escape_markdown_text(text)
    if block_multiline and any(ch in text for ch in ("\n", "\r", "\t")):
        needs_block = True
    if sanitized == "":
        return "—", needs_block, True
    return sanitized, needs_block, False


def _markdown_value_lines(value: Any) -> list[str]:
    """Return Markdown lines for a single value with sanitisation."""

    sanitized, needs_block, is_placeholder = _prepare_markdown_text(value)
    if needs_block:
        return ["```text", sanitized, "```"]
    if is_placeholder:
        return ["—"]
    return [sanitized]


def _format_list_markdown(items: Iterable[Any]) -> str:
    """Render a sequence as a markdown list."""

    lines: list[str] = []
    for item in items:
        sanitized, needs_block, is_placeholder = _prepare_markdown_text(
            item, block_multiline=True
        )
        if is_placeholder:
            continue
        if needs_block:
            block_body = _indent_block_lines(sanitized, "  ")
            lines.append("- ```text")
            lines.append(block_body)
            lines.append("  ```")
        else:
            lines.append(f"- {sanitized}")
    return "\n".join(lines)


def _format_list_plain(items: Iterable[Any]) -> str:
    """Render a sequence as plain text bullets."""

    values: list[str] = []
    for item in items:
        if item is None:
            continue
        text = str(item)
        if text == "":
            continue
        values.append(text)
    if not values:
        return ""
    return "\n".join(f"- {value}" for value in values)


def _format_citations_markdown(citations: Iterable[Any]) -> str:
    """Format citations for markdown output."""

    return _format_list_markdown(citations)


def _format_citations_plain(citations: Iterable[Any]) -> str:
    """Format citations for plain text output."""

    return _format_list_plain(citations)


def _format_reasoning_markdown(reasoning: Iterable[str]) -> str:
    """Format reasoning trace for markdown output."""

    lines: list[str] = []
    for idx, step in enumerate(reasoning, start=1):
        sanitized, needs_block, is_placeholder = _prepare_markdown_text(
            step, block_multiline=True
        )
        if is_placeholder:
            continue
        if needs_block:
            block_body = _indent_block_lines(sanitized, "   ")
            lines.append(f"{idx}. ```text")
            lines.append(block_body)
            lines.append("   ```")
        else:
            lines.append(f"{idx}. {sanitized}")
    return "\n".join(lines)


def _format_reasoning_plain(reasoning: Iterable[str]) -> str:
    """Format reasoning trace for plain text output."""

    values = [f"{idx + 1}. {step}" for idx, step in enumerate(reasoning)]
    return "\n".join(values)


def _format_metrics_markdown(metrics: Mapping[str, Any]) -> str:
    """Format metrics for markdown output."""

    if not metrics:
        return ""
    lines: list[str] = []
    for key, value in metrics.items():
        sanitized, needs_block, is_placeholder = _prepare_markdown_text(
            value, block_multiline=True
        )
        label = str(key)
        if needs_block:
            lines.append(f"- **{label}**:")
            block_body = _indent_block_lines(sanitized, "  ")
            lines.append("  ```text")
            lines.append(block_body)
            lines.append("  ```")
        else:
            display = "—" if is_placeholder else sanitized
            lines.append(f"- **{label}**: {display}")
    return "\n".join(lines)


def _format_metrics_plain(metrics: Mapping[str, Any]) -> str:
    """Format metrics for plain text output."""

    if not metrics:
        return ""
    return "\n".join(f"- {key}: {value}" for key, value in metrics.items())


def _format_knowledge_graph_markdown(summary: Optional[Mapping[str, Any]]) -> str:
    """Format knowledge graph summary details for markdown output."""

    if not summary:
        return ""

    lines: list[str] = []
    counts: list[str] = []
    entity_count = summary.get("entity_count")
    if isinstance(entity_count, (int, float)):
        counts.append(f"- **Entities**: {int(entity_count)}")
    relation_count = summary.get("relation_count")
    if isinstance(relation_count, (int, float)):
        counts.append(f"- **Relations**: {int(relation_count)}")
    contradiction_score = summary.get("contradiction_score")
    if isinstance(contradiction_score, (int, float)):
        counts.append(f"- **Contradiction score**: {float(contradiction_score):.2f}")
    if counts:
        lines.extend(counts)

    contradictions = summary.get("contradictions", [])
    if isinstance(contradictions, Iterable) and not isinstance(contradictions, (str, bytes)):
        entries = list(contradictions)
    else:
        entries = []
    if entries:
        if lines:
            lines.append("")
        lines.append("**Contradictions**")
        for item in entries:
            if isinstance(item, Mapping):
                subject = item.get("subject") or item.get("text")
                predicate = item.get("predicate")
                objects = item.get("objects")
                if subject and predicate and isinstance(objects, Iterable):
                    obj_values: list[str] = []
                    for obj in objects:
                        text = str(obj)
                        if text == "":
                            continue
                        obj_values.append(text)
                    joined = ", ".join(obj_values) if obj_values else "—"
                    lines.append(f"- {subject} — {predicate} → {joined}")
                else:
                    lines.append(f"- {json.dumps(item, ensure_ascii=False)}")
            else:
                lines.append(f"- {item}")

    paths = summary.get("multi_hop_paths", [])
    if isinstance(paths, Iterable) and not isinstance(paths, (str, bytes)):
        path_values = list(paths)
    else:
        path_values = []
    if path_values:
        if lines:
            lines.append("")
        lines.append("**Multi-hop paths**")
        for path in path_values:
            if isinstance(path, Iterable) and not isinstance(path, (str, bytes)):
                labels: list[str] = []
                for node in path:
                    text = str(node)
                    if text == "":
                        continue
                    labels.append(text)
                lines.append(f"- {' → '.join(labels) if labels else '—'}")
            else:
                lines.append(f"- {path}")

    return "\n".join(lines).strip()


def _format_knowledge_graph_plain(summary: Optional[Mapping[str, Any]]) -> str:
    """Format knowledge graph summary details for plain text output."""

    if not summary:
        return ""

    lines: list[str] = []
    counts: list[str] = []
    entity_count = summary.get("entity_count")
    if isinstance(entity_count, (int, float)):
        counts.append(f"- Entities: {int(entity_count)}")
    relation_count = summary.get("relation_count")
    if isinstance(relation_count, (int, float)):
        counts.append(f"- Relations: {int(relation_count)}")
    contradiction_score = summary.get("contradiction_score")
    if isinstance(contradiction_score, (int, float)):
        counts.append(f"- Contradiction score: {float(contradiction_score):.2f}")
    if counts:
        lines.extend(counts)

    contradictions = summary.get("contradictions", [])
    if isinstance(contradictions, Iterable) and not isinstance(contradictions, (str, bytes)):
        entries = list(contradictions)
    else:
        entries = []
    if entries:
        if lines:
            lines.append("")
        lines.append("Contradictions:")
        for item in entries:
            if isinstance(item, Mapping):
                subject = item.get("subject") or item.get("text")
                predicate = item.get("predicate")
                objects = item.get("objects")
                if subject and predicate and isinstance(objects, Iterable):
                    obj_values: list[str] = []
                    for obj in objects:
                        text = str(obj)
                        if text == "":
                            continue
                        obj_values.append(text)
                    joined = ", ".join(obj_values) if obj_values else "—"
                    lines.append(f"- {subject} — {predicate} -> {joined}")
                else:
                    lines.append(f"- {json.dumps(item, ensure_ascii=False)}")
            else:
                lines.append(f"- {item}")

    paths = summary.get("multi_hop_paths", [])
    if isinstance(paths, Iterable) and not isinstance(paths, (str, bytes)):
        path_values = list(paths)
    else:
        path_values = []
    if path_values:
        if lines:
            lines.append("")
        lines.append("Multi-hop paths:")
        for path in path_values:
            if isinstance(path, Iterable) and not isinstance(path, (str, bytes)):
                labels = [str(node) for node in path if str(node).strip()]
                lines.append(f"- {' -> '.join(labels) if labels else '—'}")
            else:
                lines.append(f"- {path}")

    return "\n".join(lines).strip()


def _format_graph_exports_markdown(exports: Mapping[str, bool]) -> str:
    """Format graph export guidance for markdown output."""

    available = [fmt for fmt, flag in exports.items() if flag]
    if not available:
        return ""

    label_map = {
        "graphml": "GraphML",
        "graph_json": "Graph JSON",
    }
    lines = []
    for fmt in available:
        label = label_map.get(fmt, fmt.upper())
        option = "graph-json" if fmt == "graph_json" else fmt
        lines.append(f"- {label}: run with `--output {option}`")
    return "\n".join(lines)


def _format_graph_exports_plain(exports: Mapping[str, bool]) -> str:
    """Format graph export guidance for plain text output."""

    available = [fmt for fmt, flag in exports.items() if flag]
    if not available:
        return ""

    label_map = {
        "graphml": "GraphML",
        "graph_json": "Graph JSON",
    }
    lines = []
    for fmt in available:
        label = label_map.get(fmt, fmt.upper())
        option = "graph-json" if fmt == "graph_json" else fmt
        lines.append(f"- {label}: run with --output {option}")
    return "\n".join(lines)


def _format_task_graph_markdown(task_graph: Optional[Mapping[str, Any]]) -> str:
    """Format planner task graph for markdown output."""

    if not task_graph:
        return ""
    tasks = task_graph.get("tasks", []) if isinstance(task_graph, Mapping) else []
    if not tasks:
        return ""

    lines: list[str] = []
    for task in tasks:
        if not isinstance(task, Mapping):
            lines.append(f"- {task}")
            continue
        task_id = str(task.get("id") or "task")
        question = str(task.get("question") or "").strip()
        headline = f"- **{task_id}**"
        if question:
            headline += f": {question}"
        lines.append(headline)

        def _join(items: Iterable[Any]) -> str:
            return ", ".join(str(item) for item in items if str(item).strip())

        tools = _join(task.get("tools", []))
        if tools:
            lines.append(f"  - Tools: {tools}")

        depends_on = _join(task.get("depends_on", []))
        if depends_on:
            lines.append(f"  - Depends on: {depends_on}")

        criteria = _join(task.get("criteria", []))
        if criteria:
            lines.append(f"  - Criteria: {criteria}")

        sub_questions = task.get("sub_questions", [])
        if isinstance(sub_questions, Iterable) and not isinstance(sub_questions, (str, bytes)):
            sub_items = [str(item).strip() for item in sub_questions if str(item).strip()]
            if sub_items:
                lines.append("  - Sub-questions:")
                lines.extend(f"    - {item}" for item in sub_items)
    return "\n".join(lines)


def _format_task_graph_plain(task_graph: Optional[Mapping[str, Any]]) -> str:
    """Format planner task graph for plain text output."""

    if not task_graph:
        return ""
    tasks = task_graph.get("tasks", []) if isinstance(task_graph, Mapping) else []
    if not tasks:
        return ""

    lines: list[str] = []
    for task in tasks:
        if not isinstance(task, Mapping):
            lines.append(f"- {task}")
            continue
        task_id = str(task.get("id") or "task")
        question = str(task.get("question") or "").strip()
        headline = f"- {task_id}"
        if question:
            headline += f": {question}"
        lines.append(headline)

        def _join(items: Iterable[Any]) -> str:
            return ", ".join(str(item) for item in items if str(item).strip())

        tools = _join(task.get("tools", []))
        if tools:
            lines.append(f"  - Tools: {tools}")

        depends_on = _join(task.get("depends_on", []))
        if depends_on:
            lines.append(f"  - Depends on: {depends_on}")

        criteria = _join(task.get("criteria", []))
        if criteria:
            lines.append(f"  - Criteria: {criteria}")

        sub_questions = task.get("sub_questions", [])
        if isinstance(sub_questions, Iterable) and not isinstance(sub_questions, (str, bytes)):
            sub_items = [str(item).strip() for item in sub_questions if str(item).strip()]
            if sub_items:
                lines.append("  - Sub-questions:")
                lines.extend(f"    - {item}" for item in sub_items)
    return "\n".join(lines)


def _format_react_traces_markdown(traces: Iterable[Mapping[str, Any]]) -> str:
    """Format ReAct traces for markdown output."""

    lines: list[str] = []
    for trace in traces:
        if not isinstance(trace, Mapping):
            lines.append(f"- {trace}")
            continue
        task_id = str(trace.get("task_id") or "task")
        step = trace.get("step")
        thought = str(trace.get("thought") or "").strip()
        header = f"- **{task_id}" + (f"#{step}" if step is not None else "") + "**"
        if thought:
            header += f": {thought}"
        lines.append(header)
        action = trace.get("action")
        if isinstance(action, str) and action.strip():
            lines.append(f"  - Action: {action.strip()}")
        observation = trace.get("observation")
        if isinstance(observation, str) and observation.strip():
            lines.append(f"  - Observation: {observation.strip()}")
        elif observation not in (None, ""):
            lines.append(f"  - Observation: {observation}")
        tool = trace.get("tool")
        if tool:
            lines.append(f"  - Tool: {tool}")
    return "\n".join(lines)


def _format_react_traces_plain(traces: Iterable[Mapping[str, Any]]) -> str:
    """Format ReAct traces for plain text output."""

    lines: list[str] = []
    for trace in traces:
        if not isinstance(trace, Mapping):
            lines.append(f"- {trace}")
            continue
        task_id = str(trace.get("task_id") or "task")
        step = trace.get("step")
        thought = str(trace.get("thought") or "").strip()
        header = f"- {task_id}" + (f"#{step}" if step is not None else "")
        if thought:
            header += f": {thought}"
        lines.append(header)
        action = trace.get("action")
        if isinstance(action, str) and action.strip():
            lines.append(f"  - Action: {action.strip()}")
        observation = trace.get("observation")
        if isinstance(observation, str) and observation.strip():
            lines.append(f"  - Observation: {observation.strip()}")
        elif observation not in (None, ""):
            lines.append(f"  - Observation: {observation}")
        tool = trace.get("tool")
        if tool:
            lines.append(f"  - Tool: {tool}")
    return "\n".join(lines)


def _render_markdown(payload: DepthPayload) -> str:
    """Render the payload as markdown text."""

    parts: list[str] = ["# TL;DR"]
    parts.extend(_markdown_value_lines(payload.tldr))
    if note := payload.notes.get("tldr"):
        parts.append(f"> {note}")

    parts.append("")
    parts.append("## Answer")
    parts.extend(_markdown_value_lines(payload.answer))

    parts.append("")
    parts.append("## Key Findings")
    key_section = _format_list_markdown(payload.key_findings)
    if key_section:
        parts.append(key_section)
    if note := payload.notes.get("key_findings"):
        parts.append(f"> {note}")

    parts.append("")
    parts.append("## Citations")
    citations_section = _format_citations_markdown(payload.citations)
    if citations_section:
        parts.append(citations_section)
    if note := payload.notes.get("citations"):
        parts.append(f"> {note}")

    parts.append("")
    parts.append("## Claim Audits")
    audits_section = _format_claim_audits_markdown(payload.claim_audits)
    if audits_section:
        parts.append(audits_section)
    if note := payload.notes.get("claim_audits"):
        parts.append(f"> {note}")

    parts.append("")
    parts.append("## Reasoning Trace")
    reasoning_section = _format_reasoning_markdown(payload.reasoning)
    if reasoning_section:
        parts.append(reasoning_section)
    if note := payload.notes.get("reasoning"):
        parts.append(f"> {note}")

    parts.append("")
    parts.append("## Metrics")
    metrics_section = _format_metrics_markdown(payload.metrics)
    if metrics_section:
        parts.append(metrics_section)
    if note := payload.notes.get("metrics"):
        parts.append(f"> {note}")

    if payload.knowledge_graph:
        parts.append("")
        parts.append("## Knowledge Graph")
        knowledge_section = _format_knowledge_graph_markdown(payload.knowledge_graph)
        if knowledge_section:
            parts.append(knowledge_section)
        if note := payload.notes.get("knowledge_graph_contradictions"):
            parts.append(f"> {note}")
        if note := payload.notes.get("knowledge_graph_paths"):
            parts.append(f"> {note}")
    elif note := payload.notes.get("knowledge_graph"):
        parts.append("")
        parts.append("## Knowledge Graph")
        parts.append(f"> {note}")

    parts.append("")
    parts.append("## Task Graph")
    task_graph_section = _format_task_graph_markdown(payload.task_graph)
    if task_graph_section:
        parts.append(task_graph_section)
    if note := payload.notes.get("task_graph"):
        parts.append(f"> {note}")

    parts.append("")
    parts.append("## ReAct Trace")
    react_section = _format_react_traces_markdown(payload.react_traces)
    if react_section:
        parts.append(react_section)
    if note := payload.notes.get("react_traces"):
        parts.append(f"> {note}")

    if payload.graph_exports:
        parts.append("")
        parts.append("## Graph Exports")
        exports_section = _format_graph_exports_markdown(payload.graph_exports)
        if exports_section:
            parts.append(exports_section)
    if note := payload.notes.get("graph_exports"):
        parts.append(f"> {note}")

    parts.append("")
    parts.append("## Depth")
    parts.extend(_markdown_value_lines(payload.depth.label))

    parts.append("")
    parts.append("## Raw Response")
    if payload.raw_response is not None:
        raw_json = json.dumps(payload.raw_response, indent=2, ensure_ascii=False)
        parts.append("```json")
        parts.append(raw_json)
        parts.append("```")
    if note := payload.notes.get("raw_response"):
        parts.append(f"> {note}")

    return "\n".join(parts).strip()


def _render_plain(payload: DepthPayload) -> str:
    """Render the payload as plain text."""

    lines: list[str] = [f"TL;DR:\n{payload.tldr or '—'}"]
    if note := payload.notes.get("tldr"):
        lines.append(note)
    lines.extend(["", f"Answer:\n{payload.answer or '—'}"])

    lines.append("")
    lines.append("Key Findings:")
    key_section = _format_list_plain(payload.key_findings)
    if key_section:
        lines.append(key_section)
    if note := payload.notes.get("key_findings"):
        lines.append(note)

    lines.append("")
    lines.append("Citations:")
    citations_section = _format_citations_plain(payload.citations)
    if citations_section:
        lines.append(citations_section)
    if note := payload.notes.get("citations"):
        lines.append(note)

    lines.append("")
    lines.append("Claim Audits:")
    audits_section = _format_claim_audits_plain(payload.claim_audits)
    if audits_section:
        lines.append(audits_section)
    if note := payload.notes.get("claim_audits"):
        lines.append(note)

    lines.append("")
    lines.append("Reasoning Trace:")
    reasoning_section = _format_reasoning_plain(payload.reasoning)
    if reasoning_section:
        lines.append(reasoning_section)
    if note := payload.notes.get("reasoning"):
        lines.append(note)

    lines.append("")
    lines.append("Metrics:")
    metrics_section = _format_metrics_plain(payload.metrics)
    if metrics_section:
        lines.append(metrics_section)
    if note := payload.notes.get("metrics"):
        lines.append(note)

    if payload.knowledge_graph:
        lines.append("")
        lines.append("Knowledge Graph:")
        knowledge_section = _format_knowledge_graph_plain(payload.knowledge_graph)
        if knowledge_section:
            lines.append(knowledge_section)
        if note := payload.notes.get("knowledge_graph_contradictions"):
            lines.append(note)
        if note := payload.notes.get("knowledge_graph_paths"):
            lines.append(note)
    elif note := payload.notes.get("knowledge_graph"):
        lines.append("")
        lines.append("Knowledge Graph:")
        lines.append(note)

    lines.append("")
    lines.append("Task Graph:")
    task_graph_section = _format_task_graph_plain(payload.task_graph)
    if task_graph_section:
        lines.append(task_graph_section)
    if note := payload.notes.get("task_graph"):
        lines.append(note)

    lines.append("")
    lines.append("ReAct Trace:")
    react_section = _format_react_traces_plain(payload.react_traces)
    if react_section:
        lines.append(react_section)
    if note := payload.notes.get("react_traces"):
        lines.append(note)

    if payload.graph_exports:
        lines.append("")
        lines.append("Graph Exports:")
        exports_section = _format_graph_exports_plain(payload.graph_exports)
        if exports_section:
            lines.append(exports_section)
    if note := payload.notes.get("graph_exports"):
        lines.append(note)

    lines.append("")
    lines.append(f"Depth: {payload.depth.label}")

    lines.append("")
    lines.append("Raw Response:")
    if payload.raw_response is not None:
        lines.append(json.dumps(payload.raw_response, indent=2, ensure_ascii=False))
    if note := payload.notes.get("raw_response"):
        lines.append(note)

    return "\n".join(lines).strip()


def _render_json(payload: DepthPayload) -> str:
    """Render the payload as JSON."""

    data: Dict[str, Any] = {
        "depth": payload.depth.label,
        "tldr": payload.tldr,
        "answer": payload.answer,
        "key_findings": [_json_safe(item) for item in payload.key_findings],
        "citations": [_json_safe(item) for item in payload.citations],
        "claim_audits": [_json_safe(item) for item in payload.claim_audits],
        "reasoning": [_json_safe(item) for item in payload.reasoning],
        "metrics": _json_safe(payload.metrics),
        "notes": payload.notes,
        "sections": payload.sections,
    }
    if payload.warnings:
        data["warnings"] = [_json_safe(item) for item in payload.warnings]
    if payload.state_id:
        data["state_id"] = payload.state_id
    if payload.task_graph is not None:
        data["task_graph"] = _json_safe(payload.task_graph)
    if payload.react_traces:
        data["react_traces"] = [_json_safe(item) for item in payload.react_traces]
    if payload.knowledge_graph:
        data["knowledge_graph"] = _json_safe(payload.knowledge_graph)
    if payload.graph_exports:
        data["graph_exports"] = _json_safe(payload.graph_exports)
    if payload.graph_export_payloads:
        data["graph_export_payloads"] = _json_safe(payload.graph_export_payloads)
    if payload.raw_response is not None:
        data["raw_response"] = _json_safe(payload.raw_response)
    return json.dumps(data, indent=2, ensure_ascii=False)


def _template_variables_from_payload(payload: DepthPayload) -> Dict[str, Any]:
    """Build template variables from a depth payload."""

    tldr_lines = _markdown_value_lines(payload.tldr)
    answer_lines = _markdown_value_lines(payload.answer)
    tldr_markdown = "\n".join(tldr_lines)
    answer_markdown = "\n".join(answer_lines)

    key_markdown = _format_list_markdown(payload.key_findings)
    key_plain = _format_list_plain(payload.key_findings)
    citations_markdown = _format_citations_markdown(payload.citations)
    citations_plain = _format_citations_plain(payload.citations)
    reasoning_markdown = _format_reasoning_markdown(payload.reasoning)
    reasoning_plain = _format_reasoning_plain(payload.reasoning)
    metrics_markdown = _format_metrics_markdown(payload.metrics)
    metrics_plain = _format_metrics_plain(payload.metrics)
    claim_audits_markdown = _format_claim_audits_markdown(payload.claim_audits)
    claim_audits_plain = _format_claim_audits_plain(payload.claim_audits)
    task_graph_markdown = _format_task_graph_markdown(payload.task_graph)
    task_graph_plain = _format_task_graph_plain(payload.task_graph)
    react_markdown = _format_react_traces_markdown(payload.react_traces)
    react_plain = _format_react_traces_plain(payload.react_traces)
    knowledge_markdown = _format_knowledge_graph_markdown(payload.knowledge_graph)
    knowledge_plain = _format_knowledge_graph_plain(payload.knowledge_graph)
    graph_exports_markdown = _format_graph_exports_markdown(payload.graph_exports)
    graph_exports_plain = _format_graph_exports_plain(payload.graph_exports)

    knowledge_section_markdown = ""
    knowledge_section_plain = ""
    if payload.knowledge_graph:
        kg_lines_markdown = ["## Knowledge Graph"]
        if knowledge_markdown:
            kg_lines_markdown.append(knowledge_markdown)
        if note := payload.notes.get("knowledge_graph_contradictions"):
            kg_lines_markdown.append(f"> {note}")
        if note := payload.notes.get("knowledge_graph_paths"):
            kg_lines_markdown.append(f"> {note}")
        knowledge_section_markdown = "\n".join(kg_lines_markdown).strip()

        kg_lines_plain = ["Knowledge Graph:"]
        if knowledge_plain:
            kg_lines_plain.append(knowledge_plain)
        if note := payload.notes.get("knowledge_graph_contradictions"):
            kg_lines_plain.append(note)
        if note := payload.notes.get("knowledge_graph_paths"):
            kg_lines_plain.append(note)
        knowledge_section_plain = "\n".join(kg_lines_plain).strip()

    graph_exports_section_markdown = ""
    graph_exports_section_plain = ""
    if payload.graph_exports:
        ge_lines_markdown = ["## Graph Exports"]
        if graph_exports_markdown:
            ge_lines_markdown.append(graph_exports_markdown)
        if note := payload.notes.get("graph_exports"):
            ge_lines_markdown.append(f"> {note}")
        graph_exports_section_markdown = "\n".join(ge_lines_markdown).strip()

        ge_lines_plain = ["Graph Exports:"]
        if graph_exports_plain:
            ge_lines_plain.append(graph_exports_plain)
        if note := payload.notes.get("graph_exports"):
            ge_lines_plain.append(note)
        graph_exports_section_plain = "\n".join(ge_lines_plain).strip()

    return {
        "tldr": tldr_markdown,
        "tldr_markdown": tldr_markdown,
        "tldr_note": payload.notes.get("tldr", ""),
        "depth_label": payload.depth.label,
        "answer": answer_markdown,
        "answer_markdown": answer_markdown,
        "answer_plain": payload.answer,
        "key_findings": key_markdown or payload.notes.get("key_findings", ""),
        "key_findings_markdown": key_markdown,
        "key_findings_plain": key_plain,
        "key_findings_list": payload.key_findings,
        "key_findings_note": payload.notes.get("key_findings", ""),
        "citations": citations_markdown or payload.notes.get("citations", ""),
        "citations_markdown": citations_markdown,
        "citations_plain": citations_plain,
        "citations_list": payload.citations,
        "citations_note": payload.notes.get("citations", ""),
        "claim_audits": claim_audits_markdown or payload.notes.get("claim_audits", ""),
        "claim_audits_markdown": claim_audits_markdown,
        "claim_audits_plain": claim_audits_plain,
        "claim_audits_note": payload.notes.get("claim_audits", ""),
        "reasoning": reasoning_markdown or payload.notes.get("reasoning", ""),
        "reasoning_markdown": reasoning_markdown,
        "reasoning_plain": reasoning_plain,
        "reasoning_list": payload.reasoning,
        "reasoning_note": payload.notes.get("reasoning", ""),
        "metrics": metrics_markdown or payload.notes.get("metrics", ""),
        "metrics_markdown": metrics_markdown,
        "metrics_plain": metrics_plain,
        "metrics_note": payload.notes.get("metrics", ""),
        "task_graph": task_graph_markdown or payload.notes.get("task_graph", ""),
        "task_graph_markdown": task_graph_markdown,
        "task_graph_plain": task_graph_plain,
        "task_graph_note": payload.notes.get("task_graph", ""),
        "react_traces": react_markdown or payload.notes.get("react_traces", ""),
        "react_traces_markdown": react_markdown,
        "react_traces_plain": react_plain,
        "react_traces_note": payload.notes.get("react_traces", ""),
        "knowledge_graph": knowledge_markdown or payload.notes.get("knowledge_graph", ""),
        "knowledge_graph_markdown": knowledge_markdown,
        "knowledge_graph_plain": knowledge_plain,
        "knowledge_graph_note": payload.notes.get("knowledge_graph", ""),
        "knowledge_graph_contradictions_note": payload.notes.get(
            "knowledge_graph_contradictions", ""
        ),
        "knowledge_graph_paths_note": payload.notes.get("knowledge_graph_paths", ""),
        "graph_exports": graph_exports_markdown or payload.notes.get("graph_exports", ""),
        "graph_exports_markdown": graph_exports_markdown,
        "graph_exports_plain": graph_exports_plain,
        "graph_exports_note": payload.notes.get("graph_exports", ""),
        "graph_export_payloads": payload.graph_export_payloads,
        "knowledge_graph_section": knowledge_section_markdown,
        "knowledge_graph_section_plain": knowledge_section_plain,
        "graph_exports_section": graph_exports_section_markdown,
        "graph_exports_section_plain": graph_exports_section_plain,
        "raw_json": (
            json.dumps(payload.raw_response, indent=2, ensure_ascii=False)
            if payload.raw_response is not None
            else ""
        ),
        "raw_response_note": payload.notes.get("raw_response", ""),
        "warnings": payload.warnings,
        "notes": payload.notes,
        "sections": payload.sections,
        "state_id": payload.state_id,
    }


class FormatTemplate(BaseModel):
    """A template for formatting query responses.

    This class represents a format template that can be used to format QueryResponse
    objects. It uses the string.Template syntax for variable substitution, where
    variables are referenced as ${variable_name} in the template text.

    Attributes:
        name: The name of the template.
        description: An optional description of the template.
        template: The template text with variable placeholders.
    """

    name: str
    description: Optional[str] = None
    template: str

    def render(
        self, response: QueryResponse, extra: Optional[Dict[str, Any]] = None
    ) -> str:
        """Render the template with the given QueryResponse."""

        variables = {
            "answer": response.answer,
            "citations": "\n".join([f"- {c}" for c in response.citations]),
            "reasoning": "\n".join([f"- {r}" for r in response.reasoning]),
            "metrics": "\n".join([f"- {k}: {v}" for k, v in response.metrics.items()]),
            "claim_audits": _format_claim_audits_markdown(response.claim_audits),
            "claim_audit_count": len(response.claim_audits),
            "tldr": response.answer,
            "tldr_note": "",
            "depth_label": OutputDepth.STANDARD.label,
            "key_findings": "",
            "key_findings_note": "",
            "citations_note": "",
            "claim_audits_note": "",
            "reasoning_note": "",
            "metrics_note": "",
            "task_graph": "",
            "task_graph_note": "",
            "react_traces": "",
            "react_traces_note": "",
            "raw_json": "",
            "raw_response_note": "",
            "sections": {},
        }

        for k, v in response.metrics.items():
            variables[f"metric_{k}"] = str(v)

        if extra:
            variables.update(extra)

        template = string.Template(self.template)
        try:
            return template.substitute(variables)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise KeyError(
                f"Missing required variable '{missing_var}' for format template '{self.name}'. "
                f"Available variables: {', '.join(variables.keys())}"
            )


class TemplateRegistry:
    """Registry for format templates.

    This class provides a centralized registry for storing and retrieving format templates.
    It maintains a dictionary of templates indexed by name and provides methods for
    registering, retrieving, and loading templates from configuration and files.
    """

    _templates: Dict[str, FormatTemplate] = {}
    _default_templates: Dict[str, Dict[str, Any]] = {
        "markdown": {
            "name": "markdown",
            "description": "Markdown format with depth-aware sections",
            "template": """# TL;DR
${tldr}

## Answer
${answer}

## Key Findings
${key_findings}
${key_findings_note}

## Citations
${citations}
${citations_note}

## Claim Audits
${claim_audits}
${claim_audits_note}

## Reasoning Trace
${reasoning}
${reasoning_note}

## Metrics
${metrics}
${metrics_note}

${knowledge_graph_section}

## Task Graph
${task_graph}
${task_graph_note}

## ReAct Trace
${react_traces}
${react_traces_note}

${graph_exports_section}

## Depth
${depth_label}

## Raw Response
${raw_json}
${raw_response_note}
""",
        },
        "plain": {
            "name": "plain",
            "description": "Simple text format for basic terminal output",
            "template": """TL;DR:
${tldr}

Answer:
${answer}

Key Findings:
${key_findings}
${key_findings_note}

Citations:
${citations}
${citations_note}

Claim Audits:
${claim_audits}
${claim_audits_note}

Reasoning Trace:
${reasoning}
${reasoning_note}

Metrics:
${metrics}
${metrics_note}

${knowledge_graph_section}

Task Graph:
${task_graph}
${task_graph_note}

ReAct Trace:
${react_traces}
${react_traces_note}

${graph_exports_section}

Raw Response:
${raw_json}
${raw_response_note}
""",
        },
    }

    @classmethod
    def register(cls, template: FormatTemplate) -> None:
        """Register a format template in the registry.

        Args:
            template: The template to register.
        """
        cls._templates[template.name] = template
        log.debug(f"Registered format template: {template.name}")

    @classmethod
    def get(cls, name: str) -> FormatTemplate:
        """Get a format template by name.

        Args:
            name: The name of the template.

        Returns:
            The format template.

        Raises:
            KeyError: If the template is not found.
        """
        if name not in cls._templates:
            # If the template is not registered, try to load it from the default templates
            if name in cls._default_templates:
                cls.register(FormatTemplate(**cls._default_templates[name]))
            else:
                # Try to load from template directory
                cls._load_template_from_file(name)

            if name not in cls._templates:
                raise KeyError(f"Format template '{name}' not found")

        return cls._templates[name]

    @classmethod
    def _load_template_from_file(cls, name: str) -> None:
        """Load a template from a file.

        Args:
            name: The name of the template.
        """
        config = ConfigLoader().config
        template_dir = getattr(config, "template_dir", None)

        if not template_dir:
            # Check common locations
            locations = [
                Path.cwd() / "templates",
                Path.home() / ".config" / "autoresearch" / "templates",
                Path("/etc/autoresearch/templates"),
            ]

            for loc in locations:
                if loc.exists() and loc.is_dir():
                    template_dir = str(loc)
                    break

        if not template_dir:
            return

        template_path = Path(template_dir) / f"{name}.tpl"

        if not template_path.exists():
            return

        try:
            with open(template_path, "r") as f:
                template_text = f.read()

            # First line can be a description
            lines = template_text.split("\n")
            description = None
            if lines and lines[0].startswith("#"):
                description = lines[0][1:].strip()
                template_text = "\n".join(lines[1:])

            template = FormatTemplate(
                name=name, description=description, template=template_text
            )
            cls.register(template)
        except Exception as e:
            log.warning(f"Failed to load template from {template_path}: {e}")

    @classmethod
    def load_from_config(cls) -> None:
        """Load templates from configuration."""
        config = ConfigLoader().config
        templates = getattr(config, "output_templates", {})

        for name, template_data in templates.items():
            if isinstance(template_data, dict) and "template" in template_data:
                try:
                    template = FormatTemplate(name=name, **template_data)
                    cls.register(template)
                except Exception as e:
                    log.warning(f"Failed to load template '{name}' from config: {e}")


class OutputFormatter:
    """Utility class for formatting query responses in various output formats.

    This class provides static methods to format QueryResponse objects into
    different output formats suitable for various contexts, such as CLI output,
    API responses, or documentation.

    The class validates that the input conforms to the QueryResponse structure
    before formatting, ensuring consistent output regardless of the source of
    the data.

    Supported formats:
        - json: Structured JSON format for programmatic consumption
        - plain/text: Simple text format for basic terminal output
        - markdown (default): Rich text format with headings and lists
        - template:<name>: Custom template format (e.g., "template:html")
    """

    @classmethod
    def _initialize(cls) -> None:
        """Initialize the formatter by loading templates from configuration."""
        try:
            TemplateRegistry.load_from_config()
        except Exception as e:
            log.warning(f"Failed to load templates from config: {e}")

    @classmethod
    def plan_response_depth(
        cls,
        result: Any,
        depth: Any = None,
        *,
        graph_preview_enabled: bool | None = None,
        graph_exports_enabled: bool | None = None,
        graph_export_formats: Iterable[str] | None = None,
        prefetch_graph_exports: bool | None = None,
    ) -> DepthPayload:
        """Return a :class:`DepthPayload` for the provided ``result``."""

        cls._initialize()

        try:
            response = (
                result
                if isinstance(result, QueryResponse)
                else QueryResponse.model_validate(result)
            )
        except ValidationError as exc:  # pragma: no cover - handled by caller
            raise AutoresearchValidationError(
                "Invalid response format", cause=exc
            ) from exc

        return build_depth_payload(
            response,
            depth,
            graph_preview_enabled=graph_preview_enabled,
            graph_exports_enabled=graph_exports_enabled,
            graph_export_formats=graph_export_formats,
            prefetch_graph_exports=prefetch_graph_exports,
        )

    @classmethod
    def render(
        cls, result: Any, format_type: str = "markdown", depth: Any = None
    ) -> str:
        """Render a query result to a string for the specified format."""

        try:
            response = (
                result
                if isinstance(result, QueryResponse)
                else QueryResponse.model_validate(result)
            )
        except ValidationError as exc:  # pragma: no cover - handled by caller
            raise AutoresearchValidationError(
                "Invalid response format", cause=exc
            ) from exc

        fmt = format_type.lower()
        payload = cls.plan_response_depth(response, depth)

        if fmt == "json":
            return _render_json(payload)
        if fmt in {"plain", "text"}:
            try:
                template = TemplateRegistry.get("plain")
            except KeyError:
                return _render_plain(payload)
            extra = _template_variables_from_payload(payload)
            overrides = {
                "key_findings": extra.get("key_findings_plain")
                or extra.get("key_findings_note", ""),
                "citations": extra.get("citations_plain")
                or extra.get("citations_note", ""),
                "claim_audits": extra.get("claim_audits_plain")
                or extra.get("claim_audits_note", ""),
                "reasoning": extra.get("reasoning_plain")
                or extra.get("reasoning_note", ""),
                "metrics": extra.get("metrics_plain")
                or extra.get("metrics_note", ""),
                "task_graph": extra.get("task_graph_plain")
                or extra.get("task_graph_note", ""),
                "react_traces": extra.get("react_traces_plain")
                or extra.get("react_traces_note", ""),
                "knowledge_graph": extra.get("knowledge_graph_plain")
                or extra.get("knowledge_graph_note", ""),
                "graph_exports": extra.get("graph_exports_plain")
                or extra.get("graph_exports_note", ""),
                "knowledge_graph_section": extra.get("knowledge_graph_section_plain", ""),
                "graph_exports_section": extra.get("graph_exports_section_plain", ""),
            }
            extra.update(overrides)
            return template.render(response, extra=extra)
        if fmt == "markdown":
            try:
                template = TemplateRegistry.get("markdown")
            except KeyError:
                return _render_markdown(payload)
            extra = _template_variables_from_payload(payload)
            overrides = {
                "key_findings": extra.get("key_findings_markdown")
                or extra.get("key_findings_note", ""),
                "citations": extra.get("citations_markdown")
                or extra.get("citations_note", ""),
                "claim_audits": extra.get("claim_audits_markdown")
                or extra.get("claim_audits_note", ""),
                "reasoning": extra.get("reasoning_markdown")
                or extra.get("reasoning_note", ""),
                "metrics": extra.get("metrics_markdown")
                or extra.get("metrics_note", ""),
                "task_graph": extra.get("task_graph_markdown")
                or extra.get("task_graph_note", ""),
                "react_traces": extra.get("react_traces_markdown")
                or extra.get("react_traces_note", ""),
                "knowledge_graph": extra.get("knowledge_graph_markdown")
                or extra.get("knowledge_graph_note", ""),
                "graph_exports": extra.get("graph_exports_markdown")
                or extra.get("graph_exports_note", ""),
                "knowledge_graph_section": extra.get("knowledge_graph_section", ""),
                "graph_exports_section": extra.get("graph_exports_section", ""),
            }
            extra.update(overrides)
            return template.render(response, extra=extra)
        if fmt.startswith("template:"):
            template_name = fmt.split(":", 1)[1]
            template = TemplateRegistry.get(template_name)
            extra = _template_variables_from_payload(payload)
            return template.render(response, extra=extra)
        if fmt == "graphml":
            return StorageManager.export_knowledge_graph_graphml()
        if fmt in {"graph-json", "graphjson"}:
            return StorageManager.export_knowledge_graph_json()
        if fmt == "graph":
            raise ValueError(
                "Graph format cannot be rendered to a string; use format() instead."
            )
        return _render_markdown(payload)

    @classmethod
    def format(
        cls, result: Any, format_type: str = "markdown", depth: Any = None
    ) -> None:
        """Validate and format a query result to the specified output format."""

        fmt = format_type.lower()
        if fmt == "graph":
            cls._initialize()
            if isinstance(result, QueryResponse):
                response = result
            else:
                response = QueryResponse.model_validate(result)
            from rich.tree import Tree
            from rich.console import Console

            tree = Tree("Knowledge Graph")
            ans_node = tree.add("Answer")
            ans_node.add(response.answer)

            citations_node = ans_node.add("Citations")
            for c in response.citations:
                citations_node.add(str(c))

            reasoning_node = tree.add("Reasoning")
            for r in response.reasoning:
                reasoning_node.add(str(r))

            metrics_node = tree.add("Metrics")
            for k, v in response.metrics.items():
                metrics_node.add(f"{k}: {v}")

            Console(file=sys.stdout, force_terminal=False, color_system=None).print(tree)
            return
        if fmt == "graphml":
            graphml = StorageManager.export_knowledge_graph_graphml()
            sys.stdout.write(graphml + ("\n" if graphml and not graphml.endswith("\n") else ""))
            return
        if fmt in {"graph-json", "graphjson"}:
            graph_json = StorageManager.export_knowledge_graph_json()
            if graph_json and not graph_json.endswith("\n"):
                graph_json += "\n"
            sys.stdout.write(graph_json)
            return

        try:
            output = cls.render(result, format_type, depth)
        except KeyError as err:
            if fmt.startswith("template:"):
                log.error(f"Template error: {err}")
                log.warning(
                    f"Template '{format_type.split(':', 1)[1]}' not found, falling back to markdown"
                )
                output = cls.render(result, "markdown", depth)
            else:
                raise
        except ValueError as err:
            log.warning(f"{err} Falling back to markdown output.")
            output = cls.render(result, "markdown", depth)

        if output and not output.endswith("\n"):
            output += "\n"
        sys.stdout.write(output)


def _format_claim_audits_markdown(audits: list[dict[str, Any]]) -> str:
    """Render claim audits as a Markdown table with status badges."""

    if not audits:
        return "No claim audits recorded."

    lines = [
        "| Claim ID | Status | Entailment | Stability | Top Source |",
        "| --- | --- | --- | --- | --- |",
    ]
    for audit in audits:
        badge = _render_status_badge(audit.get("status", "unknown"))
        entailment = audit.get("entailment_score")
        entailment_display = "—" if entailment is None else f"{entailment:.2f}"
        stability = _format_stability_cell(audit)
        sources = audit.get("sources") or []
        primary = sources[0] if sources else {}
        label = _format_source_label(primary)
        lines.append(
            "| {claim_id} | {badge} | {entailment} | {stability} | {source} |".format(
                claim_id=audit.get("claim_id", ""),
                badge=badge,
                entailment=entailment_display,
                stability=stability,
                source=label,
            )
        )
    return "\n".join(lines)


def _format_claim_audits_plain(audits: list[dict[str, Any]]) -> str:
    """Render claim audits as plain text."""

    if not audits:
        return "No claim audits recorded."
    segments = []
    for audit in audits:
        status = _render_status_badge(audit.get("status", "unknown"), plain=True)
        entailment = audit.get("entailment_score")
        entailment_display = "n/a" if entailment is None else f"{entailment:.2f}"
        stability = _format_stability_cell(audit, plain=True)
        segments.append(
            f"- Claim {audit.get('claim_id', '')}: {status}, "
            f"entailment={entailment_display}, stability={stability}"
        )
        sources = audit.get("sources") or []
        if sources:
            primary = sources[0]
            snippet = primary.get("snippet")
            if snippet:
                segments.append(f"  Top source: {snippet}")
            elif primary.get("title"):
                segments.append(f"  Top source: {primary['title']}")
            elif primary.get("url"):
                segments.append(f"  Top source: {primary['url']}")
    return "\n".join(segments)


def _render_status_badge(status: Any, *, plain: bool = False) -> str:
    """Return a textual badge for a claim status."""

    status_text = str(status)
    key = status_text.lower().strip()
    emoji, label = _STATUS_BADGES.get(key, ("⚪", status_text.title()))
    if plain:
        return label
    return f"{emoji} {label}"


def _format_stability_cell(audit: Mapping[str, Any], *, plain: bool = False) -> str:
    """Return a human-readable stability indicator for a claim audit."""

    sample_size = audit.get("sample_size")
    try:
        sample_value = None if sample_size is None else int(sample_size)
    except (TypeError, ValueError):
        sample_value = None
    variance_value = audit.get("entailment_variance")
    try:
        variance = None if variance_value is None else float(variance_value)
    except (TypeError, ValueError):
        variance = None
    instability = audit.get("instability_flag")
    if sample_value in (None, 0):
        return "n/a" if plain else "—"
    variance_label = f"σ²={variance:.3f}" if variance is not None else f"n={sample_value}"
    if bool(instability):
        prefix = "Needs review" if plain else "⚠️ Needs review"
    else:
        prefix = "Stable" if plain else "🟢 Stable"
    return f"{prefix} ({variance_label})"


def _format_source_label(source: Mapping[str, Any]) -> str:
    """Return a compact label for a source mapping."""

    if not source:
        return ""
    title = str(source.get("title") or "").strip()
    url = str(source.get("url") or "").strip()
    snippet = str(source.get("snippet") or "").strip()
    label = title or snippet or url
    if url and title:
        label = f"[{title}]({url})"
    if label and len(label) > 60:
        label = label[:57] + "..."
    return label
