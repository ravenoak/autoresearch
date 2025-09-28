# Build truthfulness evaluation harness

## Context
Phase 4 calls for automated runs of TruthfulQA, FEVER, and HotpotQA with KPI
tracking so we can measure the effect of adaptive gating, GraphRAG, and model
routing. The harness must integrate with existing telemetry and store results
for longitudinal review.

## Dependencies
- [prepare-first-alpha-release](prepare-first-alpha-release.md)
- [coordinate-deep-research-enhancement-initiative](coordinate-deep-research-enhancement-initiative.md)
- [deliver-evidence-pipeline-2-0](deliver-evidence-pipeline-2-0.md)
- [launch-session-graphrag-support](launch-session-graphrag-support.md)

## Acceptance Criteria
- Benchmark CLI or task runs curated subsets of TruthfulQA, FEVER, and
  HotpotQA.
- Harness records accuracy, citation coverage, contradiction rates, latency,
  and token usage per phase.
- Results persist to a reproducible format (DuckDB or Parquet) with metadata
  linking to configuration versions.
- STATUS.md summarizes benchmark outcomes after each scheduled run.
- Documentation covers setup, dataset licensing, and interpretation guidance.

## Status
Open
