# Handle config loader patches in storage teardown

## Context
Tests that patch `ConfigLoader.load_config` to bare objects without a
`storage` attribute still cause the autouse `cleanup_storage` fixture to fail
during teardown. After syncing the `dev-minimal` and `test` extras,
`uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1` stops in
`tests/unit/test_monitor_cli.py::test_metrics_skips_storage`, raising
`AttributeError: 'C' object has no attribute 'storage'` when
`storage.teardown(remove_db=True)` runs. A focused invocation of the same test
produces the identical teardown failure. Re-running the targeted storage suite
after resyncing the `dev-minimal`, `test`, and `docs` extras still raises the
same `AttributeError`, so coverage remains blocked until teardown handles the
patched config. The fixture loads the active configuration to locate RDF paths;
when the patched loader returns an object without `storage`,
`storage.teardown` raises. 【F:tests/unit/test_monitor_cli.py†L41-L88】
【ecec62†L1-L24】【1ffd0e†L1-L56】

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
