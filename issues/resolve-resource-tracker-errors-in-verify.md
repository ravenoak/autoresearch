# Resolve resource tracker errors in verify

## Context
`task verify` previously exited with multiprocessing resource tracker
`KeyError` messages after unit tests, preventing integration tests and
coverage from completing.

On September 17, 2025, the environment still lacks the Go Task CLI by default,
so a fresh `task verify` run has not been attempted. `task --version` continues
to report "command not found", and after syncing the `dev-minimal` and `test`
extras, `uv run python scripts/check_env.py` confirms that Go Task is the
remaining prerequisite. 【6c3849†L1-L3】【93590e†L1-L7】【7f1069†L1-L7】【57477e†L1-L26】
Targeted retries of the distributed coordination property suite and the VSS
extension loader tests complete without resource tracker errors, suggesting the
cleanup helpers remain effective when the suite reaches teardown.
【09e2a9†L1-L2】【669da8†L1-L2】 However, `uv run --extra test pytest tests/unit -q`
now fails in teardown because the monitor metrics tests patch
`ConfigLoader.load_config` to return `type("C", (), {})()`. The autouse
`cleanup_storage` fixture calls `storage.teardown(remove_db=True)` during
teardown and raises `AttributeError: 'C' object has no attribute 'storage'`, so
the suite aborts before coverage can run. 【990fdc†L1-L66】【d23bdc†L1-L66】 Until
the storage teardown regression is fixed and the Go Task CLI is available, we
still cannot exercise the full unit suite under coverage to confirm the
resource tracker fix.

## Dependencies
- [fix-duckdb-storage-schema-initialization](
  ../archive/fix-duckdb-storage-schema-initialization.md)

## Acceptance Criteria
- `task verify` completes without resource tracker errors.
- Integration tests and coverage reporting run to completion.
- Root cause and mitigation are documented.

## Status
Open
