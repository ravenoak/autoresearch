# Remediate unit tests after Orchestrator refactor

Unit tests fail following the attempted shift to an instance-based circuit
breaker manager. The refactor introduced API changes and incomplete updates that
leave tests in an inconsistent state.

## Context
- The in-progress refactor changed `_cb_manager` usage.
- Existing tests expect class-level state, causing failures and potential hangs.
- Fixtures and helper utilities may need redesign to use fresh Orchestrator
 instances per test.
- Additional failures stem from `tests/stubs/numpy.py` shadowing the real
  `numpy` package after installing full extras.

## Current Failures
- `tests/unit/test_failure_paths.py::test_external_lookup_unknown_backend`
- `tests/unit/test_failure_scenarios.py::test_external_lookup_network_failure`
- `tests/unit/test_failure_scenarios.py::test_external_lookup_unknown_backend`
- `tests/unit/test_formattemplate_property.py::test_formattemplate_render`
- `tests/unit/test_main_config_commands.py::test_config_init_command_force`
- `tests/unit/test_metrics.py::test_metrics_collection_and_endpoint`
- `tests/unit/test_orchestrator_utils.py::test_rotate_list_property`
- `tests/unit/test_orchestrator_utils.py::test_calculate_result_confidence`
- `tests/unit/test_output_formatter_property.py::test_output_formatter_json_markdown`
- `tests/unit/test_property_evaluate_weights.py::test_evaluate_weights_scale_invariant`
- `tests/unit/test_property_search.py::test_generate_queries_variants`
- `tests/unit/test_property_search.py::test_generate_queries_embeddings`
- `tests/unit/test_property_storage.py::test_pop_lru_order`
- `tests/unit/test_property_storage.py::test_pop_low_score`
- `tests/unit/test_property_vector_search.py::test_vector_search_calls_backend`
- `tests/unit/test_additional_coverage.py::test_streamlit_metrics` (error)

## Acceptance Criteria
- Unit tests are updated to accommodate the instance-level `_cb_manager`.
- Any hanging or failing tests are fixed.
- `task test:unit` passes reliably.

## Status
Open

