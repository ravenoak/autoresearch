# Research Federation Enhancements

This document captures the additions required to support workspace manifests,
workspace-aware orchestration, and the surrounding tooling for the research
federation workflow.

## Overview

The research federation enhancements enable multi-workspace collaboration through shared manifests, coordinated orchestration, and unified resource management. The system maintains workspace isolation while providing federation capabilities.

## Algorithms

- **Manifest Resolution**: Deterministic resource ID generation using SHA-256 hashing
- **Workspace Merging**: Conflict resolution through priority-based merging with timestamp arbitration
- **Resource Deduplication**: Content-based deduplication using similarity hashing
- **Federation Routing**: Load balancing across workspace orchestrators using consistent hashing

## Invariants

- Workspace isolation: No cross-workspace data leakage
- Manifest consistency: All workspace members see identical manifest state
- Resource integrity: Citations maintain provenance across federation boundaries
- Performance bounds: Federation overhead ≤ 10% of single-workspace performance

## Proof Sketch

The federation system maintains correctness through:
1. Deterministic manifest resolution prevents conflicts
2. Versioned state ensures eventual consistency
3. Cryptographic resource IDs prevent tampering
4. Isolation boundaries enforce access control

## Simulation Expectations

The federation system must handle:
- Concurrent manifest updates from multiple users
- Network partitions during federation operations
- Resource conflicts requiring manual resolution
- Performance degradation under high federation load

## Traceability

- **Manifest Storage**: `StorageManager.save_workspace_manifest`
- **Orchestration**: `FederationOrchestrator` in `src/autoresearch/federation/`
- **Resource Management**: `FederatedResourceManager`
- **Conflict Resolution**: `MergePolicy` implementations

## Workspace Manifest Model

- Manifests are persisted through `StorageManager.save_workspace_manifest`.
- Each manifest version stores the workspace slug, a friendly name, the
  version number, and an ordered list of resources.
- Resources are normalised to include a deterministic `resource_id`, the
  resource `kind`, canonical `reference`, optional metadata, and a
  `citation_required` flag that indicates whether dialectical roles must cite
  the resource.
- DuckDB contains a new `workspace_manifests` table that versions manifests
  and allows queries by `workspace_id`, `manifest_id`, or version.

## Workspace Orchestration

- `WorkspaceOrchestrator` wraps the existing orchestrator.
- Manifest context is injected onto the configuration model before the
  underlying orchestration run and removed afterwards.
- Each invocation derives workspace hints summarising manifest resources,
  repository filters, and preferred storage namespaces. The hints travel
  through the orchestrator, providing deterministic cache isolation and
  downstream retrieval constraints.
- Post-execution processing gathers citations from the response payload,
  ensures contrarian and fact-checker steps cite every required resource, and
  records metrics about coverage.
- Citation gaps raise a `CitationError`, making failed coverage visible to the
  CLI and desktop UI.

## Search and Storage Constraints

- `Search.external_lookup` accepts workspace hints and resource filters,
  annotating cache entries with workspace-specific tokens to prevent
  cross-manifest bleed-through.
- `_local_git_backend` and `_search_manifest_repository` honour manifest
  filters, producing results tagged with `workspace_resource_id` and skipping
  files outside declared globs or path prefixes.
- `storage_hybrid_lookup` restricts vector, graph, and ontology queries to the
  manifest namespaces, falling back to the default namespace only when the
  manifest does not specify an override.

## Dialectical Evidence Hooks

- Contrarian and fact-checker agents query workspace resources directly,
  storing `workspace_resource_id` and namespace metadata alongside their
  sources before citation checks execute.
- Agent metadata now tracks workspace evidence per resource, enabling
  diagnostics to confirm that resource-scoped evidence exists before coverage
  enforcement.

## CLI and Desktop Updates

- The CLI exposes `autoresearch workspace` commands to create manifests,
  inspect the latest version, and trigger debates scoped to the selected
  workspace.
- The desktop UI gains a workspace panel inside the session manager dock.
  Users can create manifests interactively, select a workspace, and start a
  debate that automatically scopes orchestration to the chosen version.
- When the workspace-aware orchestrator is unavailable, the CLI and UI fall
  back to the standard orchestration flow while emitting warnings.

## Scholarly Connectors

- `autoresearch.resources.scholarly` introduces fetchers for arXiv and
  Hugging Face Papers. The fetchers normalise metadata into
- `PaperMetadata`/`PaperDocument` structures with consistent identifiers,
  author lists, publication timestamps, and subject vocabularies. PDF, HTML,
  and Markdown assets are downloaded with retry-aware HTTP clients and stored
  as `PaperContentVariant` records that preserve checksums and source URLs.
- `ScholarlyCache` persists each content variant to deterministic cache paths
  using the namespace and provider identifier. Sidecar metadata records
  provenance (source URL, checksum, provider version, retrieval latency) and
  optional embeddings for future search operations.
- DuckDB stores cached papers in a `scholarly_papers` table managed through
  `StorageManager.save_scholarly_paper`, enabling offline replay without
  re-fetching content. The table now includes namespace-aware provenance,
  content variant paths, and supplemental asset references for UI surfacing.
- The CLI exposes `autoresearch workspace papers` commands for searching,
  ingesting, listing, and attaching cached papers to manifests. When a
  workspace slug is provided the ingest command auto-attaches the cached paper
  unless `--no-attach` is passed. Desktop users gain equivalent menu actions
  under “Resources”.
- Behaviour tests cover the offline replay scenario by seeding cached papers
  and asserting provenance survives disconnect events. Additional assertions
  confirm cached content variants are available when the network is disabled.

## Behavioural Scenarios

- Behaviour tests now include a scenario (tagged `@pending`) describing the
  expectation that contrarian and fact-checker roles cite each workspace
  resource. This documents the requirement while allowing follow-up work on
  automated verification steps.
