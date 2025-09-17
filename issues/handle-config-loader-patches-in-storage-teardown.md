# Handle config loader patches in storage teardown

## Context
Tests that patch `ConfigLoader.load_config` to bare objects without a
`storage` attribute still cause the autouse `cleanup_storage` fixture to fail
during teardown. After syncing the `dev-minimal` and `test` extras,
`uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1` stops in
`tests/unit/test_monitor_cli.py::test_metrics_skips_storage`, raising
`AttributeError: 'C' object has no attribute 'storage'` when
`storage.teardown(remove_db=True)` runs. A focused invocation of the same test
produces the identical teardown failure. The fixture loads the active
configuration to locate RDF paths; when the patched loader returns an object
without `storage`, `storage.teardown` raises. 【F:tests/unit/test_monitor_cli.py†L41-L88】
【93590e†L1-L7】【7f1069†L1-L7】【990fdc†L1-L66】【d23bdc†L1-L66】【93fac3†L10-L52】

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
