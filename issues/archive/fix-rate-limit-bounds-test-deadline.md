# Fix rate limit bounds test deadline

## Context
On 2025-09-07, `task verify` failed because `tests/unit/test_property_api_rate_limit_bounds.py::test_rate_limit_bounds`
exceeded Hypothesis' 200ms deadline. The test must complete reliably to unblock
full verification runs.

## Dependencies
- None

## Acceptance Criteria
- `test_property_api_rate_limit_bounds::test_rate_limit_bounds` runs under the
  Hypothesis deadline on typical development hardware.
- `task verify` passes the unit test phase without a DeadlineExceeded error.

## Status
Archived
