# Reactivate TestPyPI dry run

## Context
The October 5, 2025 verify and coverage sweeps finished cleanly, with
`task verify` reporting 694 passing tests and `task coverage` holding the
92.4 % floor, confirming the deterministic fallback fix and restoring the
release gate evidence.【F:baseline/logs/task-verify-20251005T031512Z.log†L1-L21】【F:baseline/logs/task-coverage-20251005T032844Z.log†L1-L24】
The preflight readiness plan and release plan now elevate TestPyPI
reactivation as the remaining gate before publish, so we need to bring
the dry run back online with fresh artefact logs for the dossier.
【F:docs/v0.1.0a1_preflight_plan.md†L44-L57】【F:docs/release_plan.md†L24-L38】

## Dependencies
- [prepare-first-alpha-release](prepare-first-alpha-release.md)

## Acceptance Criteria
- Dry-run publishing to TestPyPI is re-enabled in the release pipeline
  and executes successfully with artefact hashes recorded in
  `baseline/logs/`.
- The new dry run log, hash outputs, and coverage context are referenced
  in `docs/release_plan.md`, `STATUS.md`, and `TASK_PROGRESS.md` alongside
  the October 5 verify/coverage evidence.
- Release operators confirm the TestPyPI stage is unpaused and leave a
  short summary plus log links in this ticket.

## Status
Open
