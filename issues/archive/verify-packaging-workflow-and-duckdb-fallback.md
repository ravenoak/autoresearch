# Verify packaging workflow and DuckDB fallback

## Context
Packaging steps have not been validated, and DuckDB extension downloads may fail.
We need to verify the packaging workflow and provide a fallback when VSS extensions cannot be downloaded.

## Acceptance Criteria
- Run `uv run python -m build` and publish to TestPyPI in dry run to confirm packaging works.
- Add a fallback path so tests run when DuckDB extensions are unavailable.
- Document the verified packaging steps and fallback behavior.

## Status
Archived
