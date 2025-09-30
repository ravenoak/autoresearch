# Deliver evidence pipeline 2.0

## Context
Phase 1 of the Deep Research Enhancement Initiative requires per-claim audits,
iterative retrieval, entailment scoring, and self-checking ensembles. We must
extend the evidence pipeline so every claim is tagged with support status and
citations before synthesis completes. The release sweep now persists the gate
telemetry and audit badges, so downstream evidence exports must ingest those
fields while we continue expanding retrieval depth.
【F:baseline/logs/task-verify-20250930T174512Z.log†L1-L23】【F:docs/deep_research_upgrade_plan.md†L19-L34】

Final-answer audit documentation now records operator acknowledgement controls
and audit policy knobs. The **September 30, 2025 at 14:28 UTC** `task verify`
and **14:30 UTC** `task coverage` reruns captured after the docs refresh show
the strict typing and `A2AMessage` schema gaps still blocking automation while
the audit loop policies settle, keeping the evidence trail current without
lifting the TestPyPI hold.
【F:docs/deep_research_upgrade_plan.md†L19-L41】【F:baseline/logs/task-verify-20250930T142820Z.log†L1-L36】
【F:baseline/logs/task-coverage-20250930T143024Z.log†L1-L41】

## Dependencies
- [prepare-first-alpha-release](prepare-first-alpha-release.md)
- [coordinate-deep-research-enhancement-initiative](coordinate-deep-research-enhancement-initiative.md)
- [implement-adaptive-orchestration-gate](implement-adaptive-orchestration-gate.md)

## Acceptance Criteria
- Claim extractor identifies sentence-level assertions from drafts and
  syntheses.
- Retrieval loop expands queries, ranks snippets, and stores metadata for
  audit reproduction.
- Entailment and stability scores produce `supported`, `weak`, or `disputed`
  statuses with associated source snippets.
- Unsupported claims force revision, hedging, or removal before responses are
  emitted.
- Output schemas, documentation, and tests cover the audit data contract.

## Status
In Review
