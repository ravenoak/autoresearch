from __future__ import annotations

from typing import Any, ClassVar

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.errors import CitationError
from autoresearch.models import QueryResponse
from autoresearch.orchestration.workspace import WorkspaceOrchestrator
from autoresearch.storage import WorkspaceManifest, WorkspaceResource


class _StubStorageManager:
    manifest: ClassVar[WorkspaceManifest | None] = None

    @staticmethod
    def get_workspace_manifest(
        workspace_id: str,
        version: int | None = None,
        manifest_id: str | None = None,
    ) -> WorkspaceManifest:
        if _StubStorageManager.manifest is None:
            raise AssertionError("Manifest fixture missing for test")
        assert workspace_id == _StubStorageManager.manifest.workspace_id
        return _StubStorageManager.manifest


class _StubOrchestrator:
    latest: ClassVar["_StubOrchestrator | None"] = None
    responses: ClassVar[list[QueryResponse]] = []

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        _StubOrchestrator.latest = self

    def run_query(
        self,
        query: str,
        config: ConfigModel,
        callbacks: Any,
        *,
        agent_factory: Any,
        storage_manager: Any,
        visualize: bool,
    ) -> QueryResponse:
        self.calls.append(
            {
                "query": query,
                "workspace_manifest": getattr(config, "workspace_manifest", None),
                "workspace_id": getattr(config, "workspace_id", None),
                "workspace_manifest_version": getattr(config, "workspace_manifest_version", None),
            }
        )
        if not _StubOrchestrator.responses:
            raise AssertionError("No response configured for stub orchestrator")
        return _StubOrchestrator.responses.pop(0)


def _make_manifest(required: bool = True) -> WorkspaceManifest:
    return WorkspaceManifest(
        workspace_id="workspace-alpha",
        name="Workspace Alpha",
        version=1,
        resources=[
            WorkspaceResource(
                resource_id="wsres-required",
                kind="pdf",
                reference="https://example.org/resource.pdf",
                citation_required=required,
            ),
            WorkspaceResource(
                resource_id="wsres-optional",
                kind="web",
                reference="https://example.org/optional",
                citation_required=False,
            ),
        ],
    )


def _make_response(reasoning: list[dict[str, Any]]) -> QueryResponse:
    return QueryResponse(
        query="What is new?",
        answer="Result",
        citations=[],
        reasoning=reasoning,
        metrics={},
    )


def test_workspace_orchestrator_adds_metrics_and_restores_config() -> None:
    _StubStorageManager.manifest = _make_manifest()
    response = _make_response(
        [
            {"agent": "Contrarian Analyst", "reference": "https://example.org/resource.pdf"},
            {"agent": "Fact Checker", "resource_id": "wsres-required"},
        ]
    )
    _StubOrchestrator.responses = [response]

    orchestrator = WorkspaceOrchestrator(
        orchestrator_cls=_StubOrchestrator,
        storage_manager=_StubStorageManager,
    )
    config = ConfigModel()

    result = orchestrator.run_query("Question?", config, callbacks=None, workspace_id="workspace-alpha")

    assert result.metrics["workspace"]["workspace_id"] == "workspace-alpha"
    assert result.metrics["workspace"]["contrarian_cited"] == ["wsres-required"]
    assert result.metrics["workspace"]["fact_checker_cited"] == ["wsres-required"]

    assert not hasattr(config, "workspace_manifest")
    assert not hasattr(config, "workspace_id")
    assert not hasattr(config, "workspace_manifest_version")

    stub = _StubOrchestrator.latest
    assert stub is not None
    assert stub.calls[0]["workspace_manifest"] == _StubStorageManager.manifest.to_payload()
    assert stub.calls[0]["workspace_id"] == "workspace-alpha"
    assert stub.calls[0]["workspace_manifest_version"] == 1


def test_workspace_orchestrator_raises_when_resources_missing() -> None:
    _StubStorageManager.manifest = _make_manifest()
    response = _make_response([{"agent": "Contrarian Analyst"}])
    _StubOrchestrator.responses = [response]

    orchestrator = WorkspaceOrchestrator(
        orchestrator_cls=_StubOrchestrator,
        storage_manager=_StubStorageManager,
    )

    config = ConfigModel()

    with pytest.raises(CitationError) as excinfo:
        orchestrator.run_query("Question?", config, callbacks=None, workspace_id="workspace-alpha")

    assert excinfo.value.context["missing_resources"] == ["wsres-required"]
    assert excinfo.value.context["workspace_id"] == "workspace-alpha"
