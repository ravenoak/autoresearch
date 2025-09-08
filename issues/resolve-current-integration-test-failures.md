# Resolve current integration test failures

## Context
Recent `uv run pytest tests/integration -m "not slow and not requires_ui and not requires_vss \
and not requires_distributed" -q` runs pass most tests but still surface five failures.
`GitPython`-based tests error with
`AttributeError: 'Repo' object has no attribute 'head'`, and
`tests/integration/test_monitor_metrics.py::test_monitor_resources_cli` asserts non-zero counts.
The storage eviction simulation tuple mismatch was resolved on 2025-09-07, and the
`test_property_api_rate_limit_bounds` deadline issue is fixed. These regressions continue to block
the 0.1.0a1 preview.

As of 2025-09-08, the `task` CLI is missing, preventing `task verify` from
running and revalidating integration tests.

## Dependencies
- [fix-gitpython-integration-tests](fix-gitpython-integration-tests.md)
- [fix-monitor-resources-cli-test](fix-monitor-resources-cli-test.md)

## Acceptance Criteria
- API docs, metrics, health, and streaming endpoints return expected status codes when authenticated
  and reject missing API keys.
- Storage eviction simulation tests compare counts without tuple mismatches.
- Integration tests run without AttributeError or PicklingError exceptions from missing modules or
  pickling failures.
- `uv run pytest -q` completes with zero failing integration tests.

## Status
Open
