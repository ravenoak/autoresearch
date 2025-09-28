# Launch session GraphRAG support

## Context
Phase 3 introduces session-scoped knowledge graphs, neighbor expansion, and
contradiction checks built on existing storage primitives. We need an issue to
coordinate schema updates, graph exports, and orchestration integration.

## Dependencies
- [prepare-first-alpha-release](prepare-first-alpha-release.md)
- [coordinate-deep-research-enhancement-initiative](coordinate-deep-research-enhancement-initiative.md)
- [deliver-evidence-pipeline-2-0](deliver-evidence-pipeline-2-0.md)

## Acceptance Criteria
- Session graph builder extracts entities, relations, and community summaries
  from evidence payloads.
- Graph augmentation enriches prompts and planner tasks without exceeding
  budget limits.
- Contradiction detection feeds back into the adaptive gate and contrarian
  review paths.
- Graph artifacts (JSON or GraphML) export with each completed session and are
  referenced in output bundles.
- Documentation and diagrams explain the graph flow and operator controls.

## Status
Open
