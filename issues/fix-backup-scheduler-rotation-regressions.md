# Fix backup scheduler rotation regressions

## Context
`uv run --extra test pytest` reports failures in
`tests/unit/storage/test_backup_scheduler.py::test_scheduler_restarts_existing_timer`
and `::test_rotation_policy_removes_excess_and_stale_backups`. The scheduler
no longer cancels previous timers or enforces rotation policies, leaving
backups piled up and coverage blocked.
【7be155†L131-L170】

## Dependencies
- [prepare-first-alpha-release](prepare-first-alpha-release.md)

## Acceptance Criteria
- Backup scheduler restart logic cancels existing timers before scheduling new
  ones.
- Rotation removes excess or stale backups and retains deterministic fixtures
  expected by the tests.
- Unit tests in `tests/unit/storage/test_backup_scheduler.py` pass without
  flakiness.
- Release documentation notes the restored behaviour.

## Status
Open
