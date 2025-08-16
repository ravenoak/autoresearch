# Issue 18: Address slow unit test execution

Track the gap "Unit tests exceed reasonable execution time" discovered during testing.

## Context
Running `uv run pytest tests/unit -q` timed out after 100 seconds, indicating potential
performance issues or hanging tests.

## Acceptance Criteria
- Identify tests or fixtures causing slowdowns
- Reduce unit test runtime to finish within typical CI time limits
- Document any remaining long-running tests and rationale

## Status
Done – replaced thread `Lock` with `RLock` to avoid deadlock in `StorageManager.touch_node`; unit tests now complete within CI time limits.

## Related
- #5
