# Issue 28: Remediate unit tests after Orchestrator refactor

Unit tests fail following the attempted shift to an instance-based circuit
breaker manager. The refactor introduced API changes and incomplete updates that
leave tests in an inconsistent state.

## Context
- The in-progress refactor in [refactor orchestrator to instance-level circuit breaker](archive/refactor-orchestrator-instance-circuit-breaker.md) changed `_cb_manager` usage.
- Existing tests expect class-level state, causing failures and potential hangs.
- Fixtures and helper utilities may need redesign to use fresh Orchestrator
  instances per test.

## Current Failures
- `tests/unit/test_api_error_handling.py::test_query_endpoint_runtime_error`
- `tests/unit/test_api_error_handling.py::test_query_endpoint_invalid_response`
- `tests/unit/test_cli_help.py::test_search_loops_option`
- `tests/unit/test_cli_visualize.py::test_search_visualize_option`
- `tests/unit/test_main_cli.py::test_search_reasoning_mode_option[direct]`
- `tests/unit/test_main_cli.py::test_search_reasoning_mode_option[dialectical]`
- `tests/unit/test_main_cli.py::test_search_primus_start_option`
- `tests/unit/test_mcp_interface.py::test_client_server_roundtrip`
- `tests/unit/test_metrics.py::test_metrics_collection_and_endpoint`
- `tests/unit/test_orchestrator_errors.py::test_parallel_query_error_claims`
- `tests/unit/test_orchestrator_errors.py::test_parallel_query_timeout_claims`
- `tests/unit/test_parallel_module.py::test_execute_parallel_query_basic`
- `tests/unit/test_parallel_module.py::test_execute_parallel_query_agent_error`

## Acceptance Criteria
- Unit tests are updated to accommodate the instance-level `_cb_manager`.
- Any hanging or failing tests are fixed.
- `task test:unit` passes reliably.

## Status
Open

## Related
- [refactor orchestrator to instance-level circuit breaker](archive/refactor-orchestrator-instance-circuit-breaker.md)
