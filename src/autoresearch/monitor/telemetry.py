"""Helpers for capturing telemetry about claim audit records."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence


AUDIT_TELEMETRY_FIELDS: tuple[str, ...] = (
    "audit_id",
    "claim_id",
    "status",
    "entailment_score",
    "entailment_variance",
    "instability_flag",
    "sample_size",
    "sources",
    "provenance",
    "notes",
    "created_at",
)


def _coerce_float(value: Any) -> float | None:
    """Return ``value`` converted to float when possible."""

    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value: Any) -> int | None:
    """Return ``value`` converted to integer when possible."""

    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_bool(value: Any) -> bool | None:
    """Return ``value`` converted to bool when provided."""

    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return None


def normalize_audit_payload(audit: Mapping[str, Any]) -> dict[str, Any]:
    """Return a normalized audit payload for telemetry consumers.

    Args:
        audit: Mapping representing a persisted claim audit.

    Returns:
        dict[str, Any]: A dictionary containing the canonical telemetry fields.
    """

    claim_id = str(audit.get("claim_id", "")) if audit.get("claim_id") is not None else ""
    status_raw = audit.get("status")
    status = str(status_raw) if status_raw is not None else ""
    sources_raw = audit.get("sources")
    sources: list[dict[str, Any]] = []
    if isinstance(sources_raw, Sequence) and not isinstance(
        sources_raw, (str, bytes, bytearray)
    ):
        for source in sources_raw:
            if isinstance(source, Mapping):
                sources.append(dict(source))
    provenance_raw = audit.get("provenance")
    provenance = dict(provenance_raw) if isinstance(provenance_raw, Mapping) else {}
    notes_raw = audit.get("notes")
    notes = str(notes_raw) if notes_raw is not None else None
    audit_id_raw = audit.get("audit_id")
    audit_id = str(audit_id_raw) if audit_id_raw is not None else ""
    created_at = _coerce_float(audit.get("created_at"))

    payload: dict[str, Any] = {
        "audit_id": audit_id,
        "claim_id": claim_id,
        "status": status,
        "entailment_score": _coerce_float(audit.get("entailment_score")),
        "entailment_variance": _coerce_float(audit.get("entailment_variance")),
        "instability_flag": _coerce_bool(audit.get("instability_flag")),
        "sample_size": _coerce_int(audit.get("sample_size")),
        "sources": sources,
        "provenance": provenance,
        "notes": notes,
        "created_at": created_at,
    }
    return payload


def build_audit_telemetry(audits: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarise claim audit payloads for monitoring dashboards.

    Args:
        audits: Sequence of raw audit mappings as returned by storage APIs.

    Returns:
        dict[str, Any]: A telemetry snapshot including normalized audits,
        status counters, and derived aggregates useful for dashboards.
    """

    normalized: list[dict[str, Any]] = []
    for audit in audits:
        if not isinstance(audit, Mapping):
            continue
        normalized.append(normalize_audit_payload(audit))

    status_counts: Counter[str] = Counter()
    claim_ids: set[str] = set()
    flagged = 0
    for payload in normalized:
        status = payload.get("status")
        if status:
            status_counts[str(status)] += 1
        claim_id = payload.get("claim_id")
        if isinstance(claim_id, str) and claim_id:
            claim_ids.add(claim_id)
        if payload.get("instability_flag"):
            flagged += 1

    telemetry = {
        "audit_records": len(normalized),
        "claim_ids": sorted(claim_ids),
        "status_counts": dict(status_counts),
        "flagged_records": flagged,
        "audits": normalized,
    }
    return telemetry


__all__ = [
    "AUDIT_TELEMETRY_FIELDS",
    "normalize_audit_payload",
    "build_audit_telemetry",
]
