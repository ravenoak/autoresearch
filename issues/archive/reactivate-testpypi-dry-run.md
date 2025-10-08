# Reactivate TestPyPI dry run

## Context
The October 5, 2025 verify and coverage sweeps finished cleanly, with
`task verify` reporting 694 passing tests and `task coverage` holding the
92.4 % floor, confirming the deterministic fallback fix and restoring the
release gate evidence.【F:baseline/logs/task-verify-20251005T031512Z.log†L1-L21】
The coverage log mirrors the 92.4 % snapshot for cross-checking.
【F:baseline/logs/task-coverage-20251005T032844Z.log†L1-L24】
The preflight readiness plan and release plan now elevate TestPyPI
reactivation as the remaining gate before publish, so we need to bring
the dry run back online with fresh artefact logs for the dossier.
【F:docs/v0.1.0a1_preflight_plan.md†L44-L57】【F:docs/release_plan.md†L33-L41】

## Summary
- **2025-10-08 15:11 UTC:** `uv run task release:alpha` advanced through lint,
  strict typing, spec linting, metadata checks, and packaging before the
  coverage leg failed on the concurrent A2A interface test. Log and checksum:
  `baseline/logs/release-alpha-dry-run-20251008T151148Z.log` and
  `baseline/logs/release-alpha-dry-run-20251008T151148Z.sha256`.
  【F:baseline/logs/release-alpha-dry-run-20251008T151148Z.log†L152-L208】
- **2025-10-08 15:15 UTC:** `uv run python scripts/publish_dev.py --dry-run`
  rebuilt artefacts, confirmed the TestPyPI stage, and produced matching log
  and checksum files at
  `baseline/logs/testpypi-dry-run-20251008T151539Z.log` and
  `baseline/logs/testpypi-dry-run-20251008T151539Z.sha256`.
  【F:baseline/logs/testpypi-dry-run-20251008T151539Z.log†L1-L13】 The checksum
  record documents the digest for compliance tracking.
  【F:baseline/logs/testpypi-dry-run-20251008T151539Z.sha256†L1-L1】
- Maintainers acknowledged the dry-run evidence and agreed to keep the
  TestPyPI stage enabled for future release rehearsals while the coverage
  regression is triaged.
  【F:docs/release_plan.md†L43-L58】【F:STATUS.md†L21-L35】 The project log now
  tracks the coordination status for future rehearsals.
  【F:TASK_PROGRESS.md†L1-L15】

## Dependencies
- [prepare-first-alpha-release](../prepare-first-alpha-release.md)

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
Archived
