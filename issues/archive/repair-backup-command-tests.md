# Repair backup command tests

## Context
Backup CLI tests are failing. `tests/unit/test_cli_backup_extra.py::test_backup_restore_error`
and `tests/unit/test_main_backup_commands.py::{test_backup_restore_command,test_backup_restore_error}`
report unexpected messages and state. The backup implementation may not handle
errors consistently or storage initialization may be incomplete.

## Dependencies
- [resolve-storage-layer-test-failures](resolve-storage-layer-test-failures.md)

## Acceptance Criteria
- Backup CLI handles missing or corrupt archives gracefully.
- `tests/unit/test_cli_backup_extra.py::test_backup_restore_error` passes.
- `tests/unit/test_main_backup_commands.py` scenarios pass.
- Documentation updated with backup usage and error behavior.

## Status
Archived
