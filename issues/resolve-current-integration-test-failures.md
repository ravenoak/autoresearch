# Resolve current integration test failures

## Context
Recent `uv run pytest -q` runs pass unit tests but surface 40 failing integration tests. Failures
include unauthorized API endpoints returning 401/403, storage eviction simulations reporting tuple
mismatches, AttributeError and PicklingError exceptions, and search ranking calculations accessing
missing modules. These regressions block the 0.1.0a1 preview. As of 2025-09-07,
`task verify` additionally fails early because
`tests/unit/test_property_api_rate_limit_bounds.py::test_rate_limit_bounds`
exceeds Hypothesis' default deadline.

## Dependencies
- [fix-rate-limit-bounds-test-deadline](fix-rate-limit-bounds-test-deadline.md)

## Acceptance Criteria
- API docs, metrics, health, and streaming endpoints return expected status codes when authenticated
  and reject missing API keys.
- Storage eviction simulation tests compare counts without tuple mismatches.
- Integration tests run without AttributeError or PicklingError exceptions from missing modules or
  pickling failures.
- `uv run pytest -q` completes with zero failing integration tests.

## Status
Open
