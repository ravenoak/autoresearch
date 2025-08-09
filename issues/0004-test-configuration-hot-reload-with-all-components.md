# Issue 4: Test configuration hot-reload with all components

Track the task "Test configuration hot-reload with all components" from Phase 2 of `TASK_PROGRESS.md`.
See [TASK_PROGRESS.md](../TASK_PROGRESS.md) for overall status.

## Context
Validate that runtime configuration changes propagate correctly to
orchestrator, agents, storage, and search without restarts.

## Acceptance Criteria
- Hot-reload applies changes without restart
- All components respect updated settings
- No data loss or interruptions during reload

## Status
Done – see tests/integration/test_config_hot_reload_components.py

## Related
- #1
