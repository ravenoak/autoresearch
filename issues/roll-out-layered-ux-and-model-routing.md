# Roll out layered ux and model routing

## Context
Phases 4 and 5 culminate in layered research outputs, Socratic prompts, and
heterogeneous model routing with budget guards. We need a ticket that captures
UI, CLI, and orchestration updates plus telemetry and documentation.

## Dependencies
- [coordinate-deep-research-enhancement-initiative](coordinate-deep-research-enhancement-initiative.md)
- [deliver-evidence-pipeline-2-0](deliver-evidence-pipeline-2-0.md)
- [launch-session-graphrag-support](launch-session-graphrag-support.md)
- [build-truthfulness-evaluation-harness](build-truthfulness-evaluation-harness.md)

## Acceptance Criteria
- CLI and GUI expose depth controls, audit tables, and knowledge graph previews.
- Session export bundles include audits, planner traces, and graph artifacts.
- Socratic prompts integrate with planner/coordinator workflows.
- Model routing selects cost-appropriate backends per role and falls back when
  audits fail quality thresholds.
- Telemetry tracks token, latency, and accuracy deltas for routed queries and
  feeds STATUS.md updates.

## Status
Open
