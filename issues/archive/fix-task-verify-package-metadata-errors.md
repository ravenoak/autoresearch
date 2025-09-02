# Fix task verify package metadata errors

## Context
`task verify` previously surfaced package metadata problems when building the
distribution. Recent dry runs built the sdist and wheel without warnings,
showing the metadata is now complete.

## Dependencies

None.

## Acceptance Criteria
- Confirm `task verify` and `scripts/publish_dev.py --dry-run` build
  distributions without metadata warnings.
- Archive this ticket once multiple runs show no metadata errors.

## Status
Archived
