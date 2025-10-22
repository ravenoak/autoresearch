# Research Federation Enhancements

This document captures the additions required to support workspace manifests,
workspace-aware orchestration, and the surrounding tooling for the research
federation workflow.

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
- Post-execution processing gathers citations from the response payload,
  ensures contrarian and fact-checker steps cite every required resource, and
  records metrics about coverage.
- Citation gaps raise a `CitationError`, making failed coverage visible to the
  CLI and desktop UI.

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
  `PaperMetadata`/`PaperDocument` structures with consistent identifiers,
  author lists, and publication timestamps.
- `ScholarlyCache` persists paper content to deterministic cache paths using
  the combination of namespace and provider identifier. Sidecar metadata
  records provenance (source URL, checksum, content type, retrieval time) and
  optional embeddings for future search operations.
- DuckDB stores cached papers in a `scholarly_papers` table managed through
  `StorageManager.save_scholarly_paper`, enabling offline replay without
  re-fetching content.
- The CLI exposes `autoresearch workspace papers` commands for searching,
  ingesting, listing, and attaching cached papers to manifests. Desktop users
  gain equivalent menu actions under “Resources”.
- Behaviour tests cover the offline replay scenario by seeding cached papers
  and asserting provenance survives disconnect events.

## Behavioural Scenarios

- Behaviour tests now include a scenario (tagged `@pending`) describing the
  expectation that contrarian and fact-checker roles cite each workspace
  resource. This documents the requirement while allowing follow-up work on
  automated verification steps.
