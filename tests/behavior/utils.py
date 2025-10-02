"""Typed helpers for behavior test payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping, cast

from tests.behavior.context import BehaviorContext

PayloadDict = dict[str, Any]
"""Concrete alias for payload dictionaries shared across steps."""


def as_payload(payload: Mapping[str, Any] | None = None, /, **values: Any) -> PayloadDict:
    """Return a payload dictionary with a consistent ``dict[str, Any]`` type."""

    data: PayloadDict = dict(payload or {})
    data.update(values)
    return data


def store_payload(context: BehaviorContext, key: str, **values: Any) -> PayloadDict:
    """Update ``context`` with a typed payload dictionary and return it."""

    payload = as_payload(**values)
    context[key] = payload
    return payload


def ensure_dict(mapping: MutableMapping[str, Any] | None = None) -> MutableMapping[str, Any]:
    """Return a mutable mapping defaulting to an empty ``dict[str, Any]``."""

    if mapping is not None:
        return mapping
    return cast(MutableMapping[str, Any], {})


def empty_metrics() -> PayloadDict:
    """Provide a shared empty metrics payload for ``QueryResponse`` objects."""

    return cast(PayloadDict, {})


@dataclass(slots=True)
class BackupRestoreResult:
    """Capture restored database and RDF paths."""

    db_path: str
    rdf_path: str


def backup_restore_result(db_path: str, rdf_path: str) -> BackupRestoreResult:
    """Construct a :class:`BackupRestoreResult` for backup restore validations."""

    return BackupRestoreResult(db_path=db_path, rdf_path=rdf_path)
