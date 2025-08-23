# Address storage persistence eviction failure

## Context
The full test suite reports `StorageError` in
`test_persistence_and_eviction`, indicating ontology-backed storage is
misconfigured during persistence and eviction.

## Acceptance Criteria
- Diagnose root cause of the `StorageError`.
- Ensure persistence and eviction occur without raising errors.
- Add regression tests covering ontology store initialization.
- Document any configuration changes in docs.

## Status
Archived

