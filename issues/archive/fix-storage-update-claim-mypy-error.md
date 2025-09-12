# Fix storage update claim mypy error

## Context
`task check` reports `src/autoresearch/search/storage.py:23: error: "type[StorageManager]" has no attribute "update_claim"`.
The search helpers call a missing `StorageManager.update_claim` method. Mypy fails and the helper cannot update stored claims.

## Dependencies
None.

## Acceptance Criteria
- Implement `StorageManager.update_claim` or adjust the helper to call the correct storage API.
- `task check` passes without mypy errors.
- Documentation references the update claim capability.

## Status
Archived
