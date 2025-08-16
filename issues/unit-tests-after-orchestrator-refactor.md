# Remediate unit tests after Orchestrator refactor

Unit tests fail following the attempted shift to an instance-based circuit
breaker manager. The refactor introduced API changes and incomplete updates that
leave tests in an inconsistent state.

## Context
- The refactor changed `_cb_manager` usage from class-level to instance-level.
- Existing tests still assume class-level state, causing failures and hangs.
- Fixtures and helper utilities may need redesign to use fresh Orchestrator
  instances per test.
- Additional failures stem from `tests/stubs/numpy.py` shadowing the real
  `numpy` package after installing full extras.
- After installing development extras, `uv run pytest -q` executes but
  reports 181 failures in 7m49s. Many integration cases, such as
  `tests/integration/test_orchestrator_registered_pairs.py::test_orchestrator_all_registered_pairs`
  and `tests/integration/test_orchestrator_search_storage.py::test_orchestrator_search_storage`,
  raise `TypeError: Orchestrator.run_query() missing 1 required positional argument: 'config'`.

## Current Failures
- `tests/unit/test_additional_coverage.py::test_streamlit_metrics`
  - teardown fixture `reset_orchestration_metrics` fails: AttributeError: 'types.SimpleNamespace' object has no attribute 'set'
- `tests/unit/test_cache.py::test_search_uses_cache`
  - AttributeError: 'TinyDB' object has no attribute 'truncate'
- `tests/unit/test_cache.py::test_cache_lifecycle`
  - passes but coverage check fails (`fail-under=90`)
- `tests/unit/test_cache.py::test_cache_is_backend_specific`
  - AttributeError: 'TinyDB' object has no attribute 'truncate'
- `tests/unit/test_failure_paths.py::test_external_lookup_unknown_backend`
  - AttributeError: 'Query' object has no attribute 'query'
- `tests/unit/test_failure_scenarios.py::test_external_lookup_network_failure`
  - AttributeError: 'Query' object has no attribute 'query'
- `tests/unit/test_failure_scenarios.py::test_external_lookup_unknown_backend`
  - AttributeError: 'Query' object has no attribute 'query'
- `tests/unit/test_main_monitor_commands.py::test_serve_a2a_command`
  - assert 130 == 0
- `tests/unit/test_metrics.py::test_metrics_collection_and_endpoint`
  - assert 403 == 200
- `tests/unit/test_property_storage.py::test_pop_lru_order`
  - AssertionError: assert ['0', '1'] == ['1', '0']
- `tests/integration/test_orchestrator_registered_pairs.py::test_orchestrator_all_registered_pairs`
  - TypeError: `Orchestrator.run_query()` missing 1 required positional argument: `config`
- `tests/integration/test_orchestrator_search_storage.py::test_orchestrator_search_storage`
  - TypeError: `Orchestrator.run_query()` missing 1 required positional argument: `config`

## Acceptance Criteria
- Unit tests are updated to accommodate the instance-level `_cb_manager`.
- Any hanging or failing tests are fixed.
- `task test:unit` passes reliably.

## Status
Open

