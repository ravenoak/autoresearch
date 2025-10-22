"""Workspace-aware orchestration wrapper enforcing citation coverage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence, cast

from ..agents.registry import AgentFactory
from ..config.models import ConfigModel
from ..errors import CitationError
from ..logging_utils import get_logger
from ..models import QueryResponse
from ..storage import StorageManager, WorkspaceManifest
from .orchestrator import Orchestrator
from .types import CallbackMap

log = get_logger(__name__)


@dataclass
class _AgentCoverage:
    """Track citation coverage per agent role."""

    contrarian: set[str]
    fact_checker: set[str]


class WorkspaceOrchestrator:
    """Inject workspace manifest context and enforce resource citations."""

    def __init__(
        self,
        *,
        orchestrator_cls: type[Orchestrator] | None = None,
        storage_manager: type[StorageManager] = StorageManager,
    ) -> None:
        self._delegate = (orchestrator_cls or Orchestrator)()
        self._storage_manager = storage_manager

    def run_query(
        self,
        query: str,
        config: ConfigModel,
        callbacks: CallbackMap | None = None,
        *,
        workspace_id: str | None = None,
        manifest_version: int | None = None,
        manifest_id: str | None = None,
        agent_factory: Any | None = None,
        storage_manager: type[StorageManager] | None = None,
        visualize: bool = False,
    ) -> QueryResponse:
        """Execute a query with optional workspace manifest context."""

        manifest: WorkspaceManifest | None = None
        if workspace_id:
            manifest = self._resolve_manifest(workspace_id, manifest_version, manifest_id)
            manifest_payload = manifest.to_payload()
        else:
            manifest_payload = None

        previous_workspace_payload = getattr(config, "workspace_manifest", None)
        previous_workspace_id = getattr(config, "workspace_id", None)
        previous_manifest_version = getattr(config, "workspace_manifest_version", None)
        try:
            if manifest_payload is not None:
                setattr(config, "workspace_manifest", manifest_payload)
                setattr(config, "workspace_id", manifest.workspace_id)
                setattr(config, "workspace_manifest_version", manifest.version)

            response = self._delegate.run_query(
                query,
                config,
                callbacks,
                agent_factory=agent_factory if agent_factory is not None else AgentFactory,
                storage_manager=storage_manager or self._storage_manager,
                visualize=visualize,
            )
        finally:
            if manifest_payload is not None:
                if previous_workspace_payload is not None:
                    setattr(config, "workspace_manifest", previous_workspace_payload)
                else:
                    if hasattr(config, "workspace_manifest"):
                        delattr(config, "workspace_manifest")
                if previous_workspace_id is not None:
                    setattr(config, "workspace_id", previous_workspace_id)
                elif hasattr(config, "workspace_id"):
                    delattr(config, "workspace_id")
                if previous_manifest_version is not None:
                    setattr(config, "workspace_manifest_version", previous_manifest_version)
                elif hasattr(config, "workspace_manifest_version"):
                    delattr(config, "workspace_manifest_version")

        if manifest is None:
            return response

        coverage = self._verify_citation_coverage(response, manifest)
        self._annotate_metrics(response, manifest, coverage)

        missing_resources = [
            resource_id
            for resource_id in coverage["required_ids"]
            if resource_id not in coverage["contrarian"]
            or resource_id not in coverage["fact_checker"]
        ]
        if missing_resources:
            raise CitationError(
                "Workspace resources missing citations",
                workspace_id=manifest.workspace_id,
                manifest_id=manifest.manifest_id,
                missing_resources=missing_resources,
            )

        return response

    def _resolve_manifest(
        self,
        workspace_id: str,
        manifest_version: int | None,
        manifest_id: str | None,
    ) -> WorkspaceManifest:
        """Load the manifest requested by the caller."""

        try:
            manifest = self._storage_manager.get_workspace_manifest(
                workspace_id,
                version=manifest_version,
                manifest_id=manifest_id,
            )
        except Exception as exc:
            raise CitationError(
                "Failed to load workspace manifest",
                workspace_id=workspace_id,
                manifest_id=manifest_id,
                cause=exc,
            )
        log.debug(
            "Loaded workspace manifest",  # pragma: no cover - debug logging only
            extra={
                "workspace_id": manifest.workspace_id,
                "manifest_id": manifest.manifest_id,
                "version": manifest.version,
                "resource_count": len(manifest.resources),
            },
        )
        return manifest

    def _verify_citation_coverage(
        self,
        response: QueryResponse,
        manifest: WorkspaceManifest,
    ) -> dict[str, set[str]]:
        """Return resource identifiers cited by contrarian and fact-checker."""

        payload = response.dict()
        mentions = self._collect_mentions(payload)

        required_ids = {
            resource.resource_id
            for resource in manifest.resources
            if resource.citation_required
        }
        # Map references to resource ids for loose matching
        reference_map = {resource.reference: resource.resource_id for resource in manifest.resources}

        reasoning = payload.get("reasoning")
        coverage = _AgentCoverage(contrarian=set(), fact_checker=set())
        if isinstance(reasoning, Sequence):
            for step in reasoning:
                if not isinstance(step, Mapping):
                    continue
                agent_name = str(step.get("agent") or step.get("role") or "").lower()
                step_mentions = self._collect_mentions(step)
                resolved_ids = self._resolve_mentions(step_mentions, reference_map)
                if "contrarian" in agent_name:
                    coverage.contrarian.update(resolved_ids)
                if "fact" in agent_name:
                    coverage.fact_checker.update(resolved_ids)

        resolved_global = self._resolve_mentions(mentions, reference_map)
        coverage.contrarian.update(resolved_global)
        coverage.fact_checker.update(resolved_global)

        return {
            "contrarian": coverage.contrarian,
            "fact_checker": coverage.fact_checker,
            "required_ids": required_ids,
        }

    def _resolve_mentions(
        self,
        mentions: set[str],
        reference_map: Mapping[str, str],
    ) -> set[str]:
        """Map mention tokens into known resource identifiers."""

        resolved: set[str] = set()
        for token in mentions:
            if token in reference_map:
                resolved.add(reference_map[token])
            elif token in reference_map.values():
                resolved.add(token)
            elif token.startswith("wsres-"):
                resolved.add(token)
        return resolved

    def _collect_mentions(self, payload: Any) -> set[str]:
        """Collect resource identifiers and references from arbitrary payloads."""

        mentions: set[str] = set()
        if isinstance(payload, Mapping):
            for key, value in payload.items():
                key_lower = str(key).lower()
                if key_lower in {"resource_id", "workspace_resource_id", "source_id", "reference"}:
                    if isinstance(value, str):
                        mentions.add(value)
                    elif isinstance(value, Mapping) and "id" in value:
                        mentions.add(str(value["id"]))
                mentions.update(self._collect_mentions(value))
        elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
            for item in payload:
                mentions.update(self._collect_mentions(item))
        elif isinstance(payload, str):
            if "wsres-" in payload:
                for part in payload.split():
                    if part.startswith("wsres-"):
                        mentions.add(part.strip())
        return mentions

    def _annotate_metrics(
        self,
        response: QueryResponse,
        manifest: WorkspaceManifest,
        coverage: Mapping[str, set[str]],
    ) -> None:
        """Attach workspace telemetry to the orchestration metrics payload."""

        workspace_metrics = cast(dict[str, Any], getattr(response, "metrics", {}))
        metrics_bucket = workspace_metrics.setdefault("workspace", {})
        metrics_bucket.update(
            {
                "workspace_id": manifest.workspace_id,
                "manifest_id": manifest.manifest_id,
                "manifest_version": manifest.version,
                "resource_count": len(manifest.resources),
                "contrarian_cited": sorted(coverage["contrarian"]),
                "fact_checker_cited": sorted(coverage["fact_checker"]),
                "required_resources": sorted(coverage["required_ids"]),
            }
        )


__all__ = ["WorkspaceOrchestrator"]
