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

Structured error claims now mirror the evidence contract. `_handle_agent_error`
builds diagnostic claim dictionaries with explicit `debug` payloads, and
parallel orchestration emits the same schema for timeout and failure paths. The
unit and documentation updates confirm telemetry coverage so claim persistence
and downstream exports stay lossless.
【F:src/autoresearch/orchestration/error_handling.py†L1-L160】
【F:src/autoresearch/orchestration/parallel.py†L1-L220】
【F:tests/unit/test_orchestrator_errors.py†L1-L360】
【F:docs/orchestration.md†L1-L120】

PR5 reverification now extracts stored claims, retries audits with structured
attempt metadata, and persists outcomes through `StorageManager.persist_claim`,
while behavior coverage keeps audit badges visible in response payloads. PR4
retrieval exports GraphML/JSON artifacts with contradiction signals so the gate
and planner consume the same session metadata.
【F:src/autoresearch/orchestration/reverify.py†L73-L197】
【F:tests/unit/orchestration/test_reverify.py†L1-L80】
【F:tests/behavior/features/reasoning_modes.feature†L8-L22】
【F:src/autoresearch/knowledge/graph.py†L113-L204】
【F:src/autoresearch/search/context.py†L618-L666】

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
