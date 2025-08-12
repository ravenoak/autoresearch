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
Profiling shows `tests/unit/test_eviction.py` hanging after about 43
seconds, even when run in isolation. The suite also initially failed
with a missing `freezegun` dependency. Unit tests still exceed
acceptable runtime, so the issue remains open.

## Related
- #5
