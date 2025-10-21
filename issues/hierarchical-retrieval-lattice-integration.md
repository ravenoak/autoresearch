# Hierarchical retrieval lattice integration

## Context
Phase 6 extends the deep research program with a hierarchical retriever that
organises corpora into a semantic tree inspired by the LATTICE framework. The
workstream must deliver a prototype tree builder, calibration validation harness,
and dynamic-corpus safeguards before enabling the feature by default in the
**0.1.1** window. Evaluation goals match the ≈9 % Recall@100 and ≈5 % nDCG@10
BRIGHT improvements reported for LATTICE so we can quantify uplift relative to
existing GraphRAG paths. Telemetry and fallback logic will feed STATUS.md,
ROADMAP.md, and release planning notes to preserve auditability.
See [docs/deep_research_upgrade_plan.md](../docs/deep_research_upgrade_plan.md)
for the Phase 6 blueprint and [LATTICE hierarchical retrieval findings]
(../docs/external_research_papers/arxiv.org/2510.13217v1.md) for benchmark
details.

## Dependencies
- [coordinate-deep-research-enhancement-initiative](coordinate-deep-research-enhancement-initiative.md)
- Prototype tree builder and calibration scaffolding landing in feature branches
  tracked through the deep research coordination ticket

## Acceptance Criteria
- Prototype tree builder clusters corpus shards by intent/summary depth and
  persists traversal metadata for calibration replay.
- Calibration validation harness reproduces the LATTICE BRIGHT gains within the
  stated tolerance and documents methodology and datasets.
- Dynamic-corpus safeguards detect out-of-tree additions, trigger incremental
  rebuilds, and fall back to Phase 3 GraphRAG when calibration confidence drops
  below the validated threshold.
- Telemetry exports `hierarchical_retrieval.traversal_depth`,
  `hierarchical_retrieval.path_score`, calibration residuals, and fallback
  counters to dashboards and STATUS.md.
- Release plan and roadmap entries updated with evaluation checkpoints, target
  release window, and operator playbooks for enabling/disabling the retriever.

## Status
Open
