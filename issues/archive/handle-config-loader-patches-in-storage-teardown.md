# Handle config loader patches in storage teardown

## Context
The storage cleanup regression caused by patching
`ConfigLoader.load_config` to objects without a `storage` attribute has been
resolved. After syncing the `dev-minimal`, `test`, and `docs` extras the
targeted scenario now passes:
`uv run --extra test pytest tests/unit/test_monitor_cli.py::
test_metrics_skips_storage -q` completes without raising the prior
`AttributeError`. 【04f707†L1-L3】 The broader `-k "storage"` suite can now
progress to later tests, unblocking follow-on work.

## Dependencies
- None

## Acceptance Criteria
- Ensure storage cleanup tolerates tests that patch `ConfigLoader.load_config`
  or adjust those tests so teardown always receives a config with a
  `storage` attribute.
- `uv run pytest tests/unit -k "storage" -q --maxfail=1` completes without
  errors in a fresh environment with the `[test]` extras installed.
- `uv run pytest tests/unit -q` progresses beyond the monitor metrics tests
  without triggering `AttributeError: 'C' object has no attribute 'storage'`.
- Document the change in STATUS.md or TASK_PROGRESS.md.

## Status
Archived
