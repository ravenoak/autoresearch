# Fix storage schema and eviction tests

## Context
Storage integration tests fail.
`tests/integration/test_storage_eviction_sim.py::test_zero_budget_keeps_nodes`
reports unexpected node counts, and
`tests/integration/test_storage_schema.py::test_initialize_schema_version_without_fetchone`
plus `tests/unit/test_storage_utils.py::test_initialize_storage_creates_tables`
raise DuckDB errors.

## Dependencies
None.

## Acceptance Criteria
- Storage eviction maintains expected node counts when budget is zero.
- Schema initialization succeeds without `fetchone`.
- Unit and integration storage tests pass.
- Docs describe schema initialization and eviction guarantees.

## Status
Archived
