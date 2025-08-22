# Investigate task check, verify, and coverage failures

## Context
`task check`, `task verify`, and `task coverage` were attempted in a fresh environment but did not complete. `task check` halted at 38% of unit tests with a failure, `task verify` stalled during `mypy`, and `task coverage` was interrupted around 39% of the unit test run. No coverage report was generated.

## Acceptance Criteria
- `task check` completes successfully.
- `task verify` runs to completion.
- `task coverage` produces a coverage report and overall percentage.

## Status
Open
