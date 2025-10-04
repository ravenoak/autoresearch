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

## Tasks
- [ ] Draft layered output configuration stubs in `scripts/evaluate/` covering
  TruthfulQA, FEVER, and HotpotQA defaults (datasets, retries, artifact roots).
- [ ] Extend the evaluation CLI and Taskfile shims to consume the stubs so
  automation reads consistent layered UX modes and output directories.
- [ ] Wire telemetry exports into the harness to capture per-layer accuracy,
  latency, and token deltas for STATUS.md rollups and dashboard syncs.
- [ ] Add documentation callouts in `docs/testing_guidelines.md`,
  `docs/performance.md`, and `docs/diagrams/ux_architecture.md` explaining how
  layered transcripts will surface in each interface.

## Follow-on PRs
- [ ] Schedule PR to implement the automation pipeline once
  `prepare-first-alpha-release` and other release blockers flip to `Closed` so
  the harness lands after the current milestone ships.
- [ ] Schedule PR to expose layered transcript toggles in the CLI, Streamlit,
  and MCP adapters immediately after the automation pipeline merges.

## Status
Open
