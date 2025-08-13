# Issue 26: Monitor CLI callback test fails

The unit test `tests/unit/test_monitor_cli.py::test_monitor_prompts_and_passes_callbacks` fails with `assert 1 == 0` after running `task verify`.

## Context
`task verify` completes but the monitor CLI command exits with status 1, preventing full verification.

## Acceptance Criteria
- Investigate why the monitor CLI returns a non-zero exit code.
- Ensure the test passes and verify callbacks are invoked.
- Keep runtime under five minutes.

## Status
Open

## Related
- #23
