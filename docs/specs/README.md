# Module Specifications

This directory contains specifications for Autoresearch modules.
Each spec summarizes the module's responsibilities and links to
behavior-driven development (BDD) feature files that validate the
documented behaviour.

## Traceability summary

| Module | Spec | Tests |
| --- | --- | --- |
| `src/autoresearch/cache.py` | [cache.md](cache.md) | `../../tests/unit/test_cache.py` |
| `src/autoresearch/data_analysis.py` | [data-analysis.md](data-analysis.md) | `../../tests/unit/test_data_analysis.py`<br>`../../tests/unit/test_kuzu_polars.py`<br>`../../tests/behavior/features/data_analysis.feature` |
| `src/autoresearch/orchestration/` | [orchestration.md](orchestration.md) | `../../tests/behavior/features/orchestration_system.feature`<br>`../../tests/behavior/features/agent_orchestration.feature`<br>`../../tests/behavior/features/orchestrator_agents_integration.feature`<br>`../../tests/behavior/features/orchestrator_agents_integration_extended.feature`<br>`../../tests/behavior/features/parallel_query_execution.feature` |
| `src/autoresearch/output_format.py` | [output-format.md](output-format.md) | `../../tests/unit/test_output_format.py`<br>`../../tests/behavior/features/output_formatting.feature` |
| `src/autoresearch/search/` | [search.md](search.md) | `../../tests/behavior/features/search_cli.feature`<br>`../../tests/behavior/features/hybrid_search.feature`<br>`../../tests/behavior/features/storage_search_integration.feature`<br>`../../tests/behavior/features/local_sources.feature`<br>`../../tests/behavior/features/vector_search_performance.feature` |
| `src/autoresearch/storage.py` | [storage.md](storage.md) | `../../tests/unit/test_storage*.py`<br>`../../tests/integration/test_*storage*.py`<br>`../../tests/behavior/features/storage_search_integration.feature` |
| `src/autoresearch/synthesis.py` | [synthesis.md](synthesis.md) | `../../tests/behavior/features/synthesis.feature` |
| `src/autoresearch/tracing.py` | [tracing.md](tracing.md) | `../../tests/behavior/features/tracing.feature` |
| `src/autoresearch/a2a_interface.py` | [a2a-interface.md](a2a-interface.md) | `../../tests/unit/test_a2a_interface.py<br>../../tests/integration/test_a2a_interface.py<br>../../tests/behavior/features/a2a_interface.feature` |
| `src/autoresearch/agents/` | [agents.md](agents.md) | `../../tests/unit/test_advanced_agents.py<br>../../tests/unit/test_agents_llm.py<br>../../tests/unit/test_specialized_agents.py` |
| `src/autoresearch/api/` | [api.md](api.md) | `../../tests/unit/test_api.py<br>../../tests/unit/test_api_error_handling.py<br>../../tests/unit/test_api_imports.py` |
| `src/autoresearch/cli_backup.py` | [cli-backup.md](cli-backup.md) | `../../tests/unit/test_cli_backup_extra.py` |
| `src/autoresearch/cli_helpers.py` | [cli-helpers.md](cli-helpers.md) | `../../tests/unit/test_cli_helpers.py` |
| `src/autoresearch/cli_utils.py` | [cli-utils.md](cli-utils.md) | `../../tests/unit/test_cli_utils_extra.py` |
| `src/autoresearch/config_utils.py` | [config-utils.md](config-utils.md) | `../../tests/unit/test_streamlit_app_edgecases.py<br>../../tests/unit/test_streamlit_utils.py` |
| `src/autoresearch/config/` | [config.md](config.md) | `../../tests/unit/test_config_env_file.py<br>../../tests/unit/test_config_errors.py<br>../../tests/unit/test_config_loader_defaults.py` |
| `src/autoresearch/distributed/` | [distributed.md](distributed.md) | `../../tests/unit/test_distributed.py<br>../../tests/unit/test_distributed_extra.py<br>../../tests/integration/test_distributed_agent_storage.py` |
| `src/autoresearch/error_utils.py` | [error-utils.md](error-utils.md) | `../../tests/unit/test_error_utils_additional.py` |
| `src/autoresearch/errors.py` | [errors.md](errors.md) | `../../tests/unit/test_config_errors.py<br>../../tests/unit/test_config_validation_errors.py<br>../../tests/unit/test_errors.py` |
| `src/autoresearch/examples/` | [examples.md](examples.md) | `../../tests/unit/test_examples_package.py` |
| `src/autoresearch/extensions.py` | [extensions.md](extensions.md) | `../../tests/unit/test_vss_extension_loader.py<br>../../tests/unit/test_duckdb_storage_backend.py` |
| `src/autoresearch/kg_reasoning.py` | [kg-reasoning.md](kg-reasoning.md) | `../../tests/unit/test_kg_reasoning.py` |
| `src/autoresearch/llm/` | [llm.md](llm.md) | `../../tests/unit/test_agents_llm.py<br>../../tests/unit/test_llm_adapter.py<br>../../tests/unit/test_llm_capabilities.py` |
| `src/autoresearch/logging_utils.py` | [logging-utils.md](logging-utils.md) | `../../tests/unit/test_logging_utils.py`<br>`../../tests/unit/test_logging_utils_env.py` |
| `src/autoresearch/main/` | [main.md](main.md) | `../../tests/unit/test_main_backup_commands.py<br>../../tests/unit/test_main_cli.py<br>../../tests/unit/test_main_config_commands.py` |
| `src/autoresearch/mcp_interface.py` | [mcp-interface.md](mcp-interface.md) | `../../tests/unit/test_mcp_interface.py<br>../../tests/behavior/features/mcp_interface.feature` |
| `src/autoresearch/models.py` | [models.md](models.md) | `../../tests/unit/test_models_docstrings.py` |
| `src/autoresearch/monitor/` | [monitor.md](monitor.md) | `../../tests/unit/test_main_monitor_commands.py<br>../../tests/unit/test_monitor_cli.py<br>../../tests/unit/test_resource_monitor_gpu.py` |
| `src/autoresearch/resource_monitor.py` | [resource-monitor.md](resource-monitor.md) | `../../tests/unit/test_resource_monitor_gpu.py` |
| `src/autoresearch/storage_backends.py` | [storage-backends.md](storage-backends.md) | `../../tests/unit/test_duckdb_storage_backend.py<br>../../tests/unit/test_duckdb_storage_backend_extended.py` |
| `src/autoresearch/storage_backup.py` | [storage-backup.md](storage-backup.md) | `../../tests/unit/test_storage_backup.py` |
| `src/autoresearch/streamlit_app.py` | [streamlit-app.md](streamlit-app.md) | `../../tests/unit/test_streamlit_app_edgecases.py` |
| `src/autoresearch/streamlit_ui.py` | [streamlit-ui.md](streamlit-ui.md) | `../../tests/unit/test_streamlit_ui_helpers.py` |
| `src/autoresearch/test_tools.py` | [test-tools.md](test-tools.md) | `../../tests/unit/test_test_tools.py` |
| `src/autoresearch/visualization.py` | [visualization.md](visualization.md) | `../../tests/unit/test_visualization.py<br>../../tests/behavior/features/visualization_cli.feature` |

## Mapping specs to tests

- Specs reference the feature files in `tests/behavior/features/` that
  exercise the described behavior.
- When adding new behaviour or features, create or update a feature file
  and link to it from the relevant spec.

## Extending specs

1. Create a new spec file in this directory named after the module.
2. Describe the module's purpose and key workflows.
3. List the associated modules and test files under a **Traceability**
   section using relative links (e.g.,
   `../../tests/behavior/features/example.feature`).
4. Run `task verify` to ensure the new documentation and tests pass.
