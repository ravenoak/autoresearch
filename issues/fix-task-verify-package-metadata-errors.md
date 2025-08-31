# Fix task verify package metadata errors

## Context
Earlier attempts to run `task verify` surfaced package metadata problems
when building the distribution. The latest run on **August 31, 2025** built the
sdist and wheel without errors, but the issue remains open pending further
validation.

## Dependencies

None.

## Acceptance Criteria
- Confirm `task verify` and `scripts/publish_dev.py --dry-run` build distributions
  without metadata warnings.
- Remove this ticket once multiple runs show no metadata errors.

## Status
Open
