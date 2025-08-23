# Investigate backup schedule command test failure

## Context
The `task coverage` command fails because
`tests/unit/test_main_backup_commands.py::test_backup_schedule_command` asserts
`130 == 0`, blocking coverage metrics.

## Acceptance Criteria
- Determine why `test_backup_schedule_command` fails.
- Update code or test so `task coverage` passes.
- Ensure coverage data is generated and meets 90% threshold.

## Status
Open
