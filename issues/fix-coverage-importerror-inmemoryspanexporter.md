# Fix coverage task ImportError

## Context
`uv run task coverage` fails with `ImportError: cannot import name
'InMemorySpanExporter'` from `opentelemetry.sdk.trace.export`. This blocks the
full coverage run and forces documentation to record 0% coverage.

## Dependencies
- none

## Acceptance Criteria
- `uv run task coverage` completes without the ImportError.
- `scripts/update_coverage_docs.py` records the actual coverage percentage.
- Issue is archived after coverage succeeds.

## Status
Open
