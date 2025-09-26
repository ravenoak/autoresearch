"""Utilities for presenting depth-aware provenance details in UIs."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping

from ..output_format import DepthPayload, OutputDepth


def generate_socratic_prompts(
    payload: DepthPayload, max_prompts: int = 3
) -> List[str]:
    """Derive Socratic follow-up prompts from a depth payload."""

    prompts: List[str] = []
    if payload.key_findings:
        prompts.append(
            f"Which assumptions support the claim '{payload.key_findings[0]}'?"
        )
    if payload.citations:
        prompts.append(
            "If the top citation were unreliable, how would the conclusion change?"
        )
    if payload.claim_audits:
        first_claim = payload.claim_audits[0].get("claim_id", "the leading claim")
        prompts.append(
            f"What additional evidence would strengthen verification of {first_claim}?"
        )
    prompts.append(
        "Which counterexamples could challenge the TL;DR and should be investigated?"
    )
    unique_prompts = []
    for prompt in prompts:
        if prompt not in unique_prompts:
            unique_prompts.append(prompt)
    return unique_prompts[:max_prompts]


def extract_graphrag_artifacts(metrics: Mapping[str, Any]) -> Dict[str, Any]:
    """Filter metric entries that describe GraphRAG provenance artefacts."""

    artifacts: Dict[str, Any] = {}
    for key, value in metrics.items():
        key_lower = str(key).lower()
        if any(token in key_lower for token in ("graphrag", "graph_rag", "graphviz")):
            artifacts[key] = value
        elif "graph" in key_lower and isinstance(value, (dict, list)):
            artifacts[key] = value
    return artifacts


def depth_sequence() -> List[OutputDepth]:
    """Return the ordered depth options for UI widgets."""
    return [OutputDepth.TLDR, OutputDepth.CONCISE, OutputDepth.STANDARD, OutputDepth.TRACE]


def audit_status_rollup(claim_audits: List[Mapping[str, Any]]) -> Dict[str, int]:
    """Summarise claim audit statuses for quick provenance overviews."""

    if not claim_audits:
        return {}

    counts: Dict[str, int] = {}
    for audit in claim_audits:
        status = str(audit.get("status", "unknown")).lower()
        counts[status] = counts.get(status, 0) + 1

    ordered: Dict[str, int] = {}
    for key in ("supported", "needs_review", "unsupported"):
        value = counts.pop(key, 0)
        if value:
            ordered[key] = value
    for key in sorted(counts):
        if counts[key]:
            ordered[key] = counts[key]
    return ordered


def section_toggle_defaults(payload: DepthPayload) -> Dict[str, Dict[str, bool]]:
    """Return toggle availability and defaults for depth-aware sections."""

    sections = payload.sections
    return {
        "tldr": {
            "available": sections.get("tldr", True),
            "value": sections.get("tldr", True),
        },
        "key_findings": {
            "available": sections.get("key_findings", False),
            "value": sections.get("key_findings", False),
        },
        "claim_audits": {
            "available": sections.get("claim_audits", False),
            "value": sections.get("claim_audits", False),
        },
        "full_trace": {
            "available": sections.get("reasoning", False)
            or sections.get("react_traces", False),
            "value": sections.get("reasoning", False)
            or sections.get("react_traces", False),
        },
    }
