# Handle config loader patches in storage teardown

## Context
Tests that patch `ConfigLoader.load_config` to bare objects without a
`storage` attribute now cause the autouse `cleanup_storage` fixture to fail
during teardown. `test_metrics_skips_storage` in
`tests/unit/test_monitor_cli.py` replaces the loader with `type("C", (), {})()`
and the fixture subsequently raises `AttributeError: 'C' object has no
attribute 'storage'` when `storage.teardown(remove_db=True)` runs.
`uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1` stops at
that failure, so `uv run --extra test pytest tests/unit -q` never reaches the
remaining suites. The fixture loads the active configuration to locate RDF
paths; when the patched loader returns an object without `storage`,
`storage.teardown` raises. 【F:tests/unit/test_monitor_cli.py†L41-L88】
【529dfa†L1-L57】【a3c726†L25-L38】【93fac3†L10-L52】

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
