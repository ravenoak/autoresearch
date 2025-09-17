# Handle config loader patches in storage teardown

## Context
Tests that patch `ConfigLoader.load_config` to bare objects without a
`storage` attribute now cause the autouse `cleanup_storage` fixture to fail
during teardown. `test_metrics_skips_storage` in
`tests/unit/test_monitor_cli.py` replaces the loader with `type("C", (), {})()`
and the fixture subsequently raises `AttributeError: 'C' object has no
attribute 'storage'` when `storage.teardown(remove_db=True)` runs.
`uv run pytest tests/unit -k "storage" -q --maxfail=1` stops at that failure,
so `uv run pytest tests/unit -q` never reaches the remaining suites.
【F:tests/unit/test_monitor_cli.py†L41-L85】【d541c6†L1-L58】【35a0a9†L63-L73】

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
Open
