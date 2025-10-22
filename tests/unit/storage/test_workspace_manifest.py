from __future__ import annotations

import copy
from typing import Any, Mapping, cast

import networkx as nx

from autoresearch.storage import (
    StorageContext,
    StorageManager,
    StorageState,
    WorkspaceManifest,
    WorkspaceResource,
)
from autoresearch.storage_backends import DuckDBStorageBackend


class _StubManifestBackend:
    """DuckDB manifest stub capturing persisted payloads."""

    def __init__(self, *, next_versions: list[int] | None = None) -> None:
        self.persisted: list[dict[str, Any]] = []
        self.version_calls: list[str] = []
        self._versions = list(next_versions or [1])

    def persist_workspace_manifest(self, payload: Mapping[str, Any]) -> None:
        self.persisted.append(copy.deepcopy(dict(payload)))

    def next_workspace_manifest_version(self, workspace_id: str) -> int:
        self.version_calls.append(workspace_id)
        if not self._versions:
            raise AssertionError("No manifest versions configured for stub backend")
        return self._versions.pop(0)


def _make_storage_context(backend: _StubManifestBackend) -> tuple[StorageContext, StorageState]:
    context = StorageContext(
        graph=nx.DiGraph(),
        kg_graph=nx.MultiDiGraph(),
        db_backend=cast(DuckDBStorageBackend, backend),
        rdf_store=cast(Any, object()),
    )
    state = StorageState(context=context)
    return context, state


def test_save_workspace_manifest_assigns_next_version() -> None:
    backend = _StubManifestBackend(next_versions=[7])
    context, state = _make_storage_context(backend)

    original_context = StorageManager.context
    original_state = StorageManager.state

    try:
        StorageManager.context = context
        StorageManager.state = state

        saved = StorageManager.save_workspace_manifest(
            {
                "name": "Quantum Workspace",
                "resources": [
                    {
                        "kind": "pdf",
                        "reference": "https://example.org/quantum.pdf",
                        "metadata": {"title": "Quantum"},
                    }
                ],
                "annotations": {"discipline": "physics"},
            }
        )

        assert saved.version == 7
        assert saved.workspace_id == "quantum-workspace"
        assert backend.version_calls == ["quantum-workspace"]
        assert backend.persisted[0]["version"] == 7
        resource_payload = backend.persisted[0]["resources"][0]
        assert resource_payload["resource_id"] == saved.resources[0].resource_id
        assert resource_payload["citation_required"] is True
    finally:
        StorageManager.context = original_context
        StorageManager.state = original_state


def test_save_workspace_manifest_respects_provided_version() -> None:
    backend = _StubManifestBackend(next_versions=[3])
    context, state = _make_storage_context(backend)

    original_context = StorageManager.context
    original_state = StorageManager.state

    try:
        StorageManager.context = context
        StorageManager.state = state

        manifest = WorkspaceManifest(
            workspace_id="analysis-lab",
            name="Analysis Lab",
            version=5,
            resources=[
                WorkspaceResource(
                    resource_id="wsres-custom",
                    kind="dataset",
                    reference="s3://datasets/lab.csv",
                    citation_required=False,
                )
            ],
        )

        saved = StorageManager.save_workspace_manifest(manifest, increment_version=False)

        assert saved.version == 5
        assert backend.version_calls == []
        assert backend.persisted[0]["version"] == 5
        assert backend.persisted[0]["resources"][0]["citation_required"] is False
    finally:
        StorageManager.context = original_context
        StorageManager.state = original_state
