# Remediate unit tests after Orchestrator refactor

Unit tests fail following the attempted shift to an instance-based circuit
breaker manager. The refactor introduced API changes and incomplete updates that
leave tests in an inconsistent state.

## Context
- Environment setup now includes `task`, `flake8`, `typer`, and other dev
  dependencies.
- The refactor changed `_cb_manager` usage from class-level to instance-level.
- Existing tests still assume class-level state, causing failures and hangs.
- Fixtures and helper utilities may need redesign to use fresh Orchestrator
  instances per test.
- Additional failures stem from `tests/stubs/numpy.py` shadowing the real
  `numpy` package after installing full extras.

## Current Failures
- `tests/unit/test_additional_coverage.py::test_streamlit_metrics` (error - metrics teardown)
- `tests/unit/test_cache.py::test_search_uses_cache` (TinyDB `truncate` missing)
- `tests/unit/test_cache.py::test_cache_lifecycle`
- `tests/unit/test_cache.py::test_cache_is_backend_specific`
- `tests/unit/test_failure_paths.py::test_external_lookup_unknown_backend`
- `tests/unit/test_failure_scenarios.py::test_external_lookup_network_failure`
- `tests/unit/test_failure_scenarios.py::test_external_lookup_unknown_backend`

## Acceptance Criteria
- Unit tests are updated to accommodate the instance-level `_cb_manager`.
- Any hanging or failing tests are fixed.
- `task test:unit` passes reliably.

## Status
Open

