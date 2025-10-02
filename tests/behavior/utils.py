"""Typed helpers for composing and storing behavior test payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import (
    Any,
    Iterable,
    Mapping,
    MutableMapping,
    NotRequired,
    Sequence,
    TypedDict,
    cast,
)
from unittest.mock import MagicMock

from tests.behavior.context import BehaviorContext

PayloadDict = dict[str, Any]
"""Concrete alias for payload dictionaries shared across steps."""


@dataclass(slots=True)
class TempFileRecord:
    """Representation of a tracked temporary file descriptor and path."""

    fd: int
    path: str


class CleanupExtendedPayload(TypedDict, total=False):
    """Schema for the cleanup verification context shared across steps."""

    temp_files: list[TempFileRecord]
    env_vars: dict[str, str]
    original_env: dict[str, str]
    cleanup_errors: list[str]
    expect_error: bool
    mock_cleanup: MagicMock
    cleanup_error: Exception


class ScoutClaimAudit(TypedDict):
    """Schema for audit details attached to scout claims."""

    claim_id: str
    status: str
    entailment: float
    sources: list[str]
    stability: NotRequired[float]


class ScoutClaim(TypedDict):
    """Structured representation of scout claim payload entries."""

    id: str
    type: str
    content: str
    audit: NotRequired[ScoutClaimAudit]


class ScoutSource(TypedDict):
    """Schema for scout source metadata shared across steps."""

    source_id: str
    title: str
    snippet: str
    backend: str
    url: str


class ScoutComplexityFeatures(TypedDict, total=False):
    """Complexity metrics captured alongside scout samples."""

    hops: int
    entities: list[str]
    clauses: int


class ScoutEntailmentScore(TypedDict, total=False):
    """Per-claim entailment/conflict scores emitted by scout agents."""

    support: float
    conflict: float


class ScoutMetadata(TypedDict, total=False):
    """Aggregate metadata emitted with scout payloads."""

    scout_retrieval_sets: list[list[str]]
    scout_complexity_features: ScoutComplexityFeatures
    scout_entailment_scores: list[ScoutEntailmentScore]
    audit_badges: Mapping[str, int]


class AsyncSubmissionPayload(TypedDict):
    """Normalized payload returned from async API submissions in tests."""

    response: Any
    recovery_info: MutableMapping[str, str]
    logs: list[str]
    state: MutableMapping[str, Any]


def as_payload(payload: Mapping[str, Any] | None = None, /, **values: Any) -> PayloadDict:
    """Return a payload dictionary with a consistent ``dict[str, Any]`` type."""

    data: PayloadDict = dict(payload or {})
    data.update(values)
    return data


def build_cleanup_payload() -> CleanupExtendedPayload:
    """Create the default payload used by cleanup verification steps."""

    payload: CleanupExtendedPayload = {
        "temp_files": [],
        "env_vars": {},
        "original_env": {},
        "cleanup_errors": [],
    }
    return payload


def ensure_cleanup_payload(context: BehaviorContext) -> CleanupExtendedPayload:
    """Cast ``context`` to :class:`CleanupExtendedPayload` for typed access."""

    return cast(CleanupExtendedPayload, context)


def store_payload(
    context: BehaviorContext,
    key: str,
    payload: Mapping[str, Any] | None = None,
    /,
    **values: Any,
) -> PayloadDict:
    """Update ``context`` with a typed payload dictionary and return it.

    Args:
        context: The behavior context being updated.
        key: The lookup key for the stored payload.
        payload: Optional base mapping to merge into the stored payload.
        **values: Additional key-value pairs merged into the payload.

    Returns:
        The merged payload stored in ``context``.
    """

    payload = as_payload(payload, **values)
    context[key] = payload
    return payload


def ensure_dict(mapping: BehaviorContext | None = None) -> BehaviorContext:
    """Return a mutable mapping defaulting to an empty ``BehaviorContext``."""

    if mapping is not None:
        return mapping
    context: BehaviorContext = {}
    return context


def empty_metrics() -> PayloadDict:
    """Provide a shared empty metrics payload for ``QueryResponse`` objects."""

    return cast(PayloadDict, {})


def build_scout_audit(
    *,
    claim_id: str,
    status: str,
    entailment: float,
    sources: Sequence[str],
    stability: float | None = None,
) -> ScoutClaimAudit:
    """Create a :class:`ScoutClaimAudit` entry with defensive copying."""

    audit: ScoutClaimAudit = {
        "claim_id": claim_id,
        "status": status,
        "entailment": entailment,
        "sources": list(sources),
    }
    if stability is not None:
        audit["stability"] = stability
    return audit


def build_scout_claim(
    *,
    claim_id: str,
    claim_type: str,
    content: str,
    audit: ScoutClaimAudit | Mapping[str, Any] | None = None,
) -> ScoutClaim:
    """Create a :class:`ScoutClaim` optionally including audit information."""

    claim: ScoutClaim = {
        "id": claim_id,
        "type": claim_type,
        "content": content,
    }
    if audit is not None:
        claim["audit"] = cast(ScoutClaimAudit, dict(audit))
    return claim


def build_scout_source(
    *,
    source_id: str,
    title: str,
    snippet: str,
    backend: str,
    url: str,
) -> ScoutSource:
    """Create a :class:`ScoutSource` entry used in scout payload snapshots."""

    return {
        "source_id": source_id,
        "title": title,
        "snippet": snippet,
        "backend": backend,
        "url": url,
    }


def build_scout_metadata(
    *,
    retrieval_sets: Sequence[Sequence[str]] | None = None,
    complexity_features: Mapping[str, Any] | None = None,
    entailment_scores: Sequence[Mapping[str, float]] | None = None,
    audit_badges: Mapping[str, int] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> ScoutMetadata:
    """Compose :class:`ScoutMetadata` entries with optional components."""

    metadata: ScoutMetadata = {}
    if retrieval_sets is not None:
        metadata["scout_retrieval_sets"] = [list(group) for group in retrieval_sets]
    if complexity_features is not None:
        metadata["scout_complexity_features"] = cast(
            ScoutComplexityFeatures, dict(complexity_features)
        )
    if entailment_scores is not None:
        metadata["scout_entailment_scores"] = [
            cast(ScoutEntailmentScore, dict(score)) for score in entailment_scores
        ]
    if audit_badges is not None:
        metadata["audit_badges"] = dict(audit_badges)
    if extra is not None:
        extended = cast(MutableMapping[str, Any], metadata)
        extended.update(dict(extra))
    return metadata


def build_scout_payload(
    *,
    claims: Sequence[ScoutClaim] | None = None,
    results: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
    sources: Sequence[ScoutSource] | None = None,
    claim_audits: Sequence[ScoutClaimAudit] | None = None,
) -> PayloadDict:
    """Create a normalized payload for scout agent outputs."""

    payload = as_payload()
    if claims is not None:
        payload["claims"] = [dict(claim) for claim in claims]
    if results is not None:
        payload["results"] = dict(results)
    if metadata is not None:
        payload["metadata"] = dict(metadata)
    if sources is not None:
        payload["sources"] = [dict(source) for source in sources]
    if claim_audits is not None:
        payload["claim_audits"] = [dict(audit) for audit in claim_audits]
    return payload


def build_async_submission_payload(
    *,
    response: Any,
    recovery_info: Mapping[str, str] | None = None,
    logs: Iterable[str] | None = None,
    state: Mapping[str, Any] | None = None,
) -> AsyncSubmissionPayload:
    """Construct a normalized payload for async API submission checks."""

    payload: AsyncSubmissionPayload = {
        "response": response,
        "recovery_info": dict(recovery_info or {}),
        "logs": list(logs or []),
        "state": dict(state or {}),
    }
    return payload


@dataclass(slots=True)
class BackupRestoreResult:
    """Capture restored database and RDF paths."""

    db_path: str
    rdf_path: str


def backup_restore_result(db_path: str, rdf_path: str) -> BackupRestoreResult:
    """Construct a :class:`BackupRestoreResult` for backup restore validations."""

    return BackupRestoreResult(db_path=db_path, rdf_path=rdf_path)
