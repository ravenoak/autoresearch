# Resolve current integration test failures

## Context
Recent `uv run pytest tests/integration -m "not slow and not requires_ui and not requires_vss \
and not requires_distributed" -q` runs now pass GitPython and resource monitor tests, but
`tests/integration/test_storage_baseline.py::test_ram_budget_respects_baseline` fails with
`StorageError: Ontology reasoning interrupted`.
The storage eviction simulation tuple mismatch and `test_property_api_rate_limit_bounds`
deadline issue were resolved earlier, yet this remaining failure continues to block the
0.1.0a1 preview.

## Dependencies
- None

## Acceptance Criteria
- API docs, metrics, health, and streaming endpoints return expected status codes when authenticated
  and reject missing API keys.
- Storage eviction simulation tests compare counts without tuple mismatches.
- Integration tests run without `StorageError` from ontology reasoning timeouts.
- `tests/integration/test_storage_baseline.py::test_ram_budget_respects_baseline` passes.
- `uv run pytest -q` completes with zero failing integration tests.

## Status
Open
