# Module Specifications

This directory contains specifications for Autoresearch modules.
Each spec summarizes the module's responsibilities and links to
behavior-driven development (BDD) feature files that validate the
documented behaviour.

## Traceability summary

| Module | Spec | Tests |
| --- | --- | --- |
| `src/autoresearch/cache.py` | [cache.md](cache.md) | `../../tests/unit/test_cache.py`<br>`../../tests/behavior/features/cache_management.feature` |
| `src/autoresearch/data_analysis.py` | [data-analysis.md](data-analysis.md) | `../../tests/unit/test_data_analysis.py`<br>`../../tests/unit/test_kuzu_polars.py`<br>`../../tests/behavior/features/data_analysis.feature` |
| `src/autoresearch/orchestration/` | [orchestration.md](orchestration.md) | `../../tests/behavior/features/orchestration_system.feature`<br>`../../tests/behavior/features/agent_orchestration.feature`<br>`../../tests/behavior/features/orchestrator_agents_integration.feature`<br>`../../tests/behavior/features/orchestrator_agents_integration_extended.feature`<br>`../../tests/behavior/features/parallel_query_execution.feature` |
| `src/autoresearch/output_format.py` | [output-format.md](output-format.md) | `../../tests/unit/test_output_format.py`<br>`../../tests/unit/test_template.py`<br>`../../tests/behavior/features/output_formatting.feature` |
| `src/autoresearch/search/` | [search.md](search.md) | `../../tests/behavior/features/search_cli.feature`<br>`../../tests/behavior/features/hybrid_search.feature`<br>`../../tests/behavior/features/storage_search_integration.feature`<br>`../../tests/behavior/features/local_sources.feature`<br>`../../tests/behavior/features/vector_search_performance.feature` |
| `src/autoresearch/storage.py` | [storage.md](storage.md) | `../../tests/unit/test_storage*.py`<br>`../../tests/integration/test_*storage*.py`<br>`../../tests/behavior/features/storage_search_integration.feature` |
| `src/autoresearch/synthesis.py` | [synthesis.md](synthesis.md) | `../../tests/behavior/features/synthesis.feature` |
| `src/autoresearch/tracing.py` | [tracing.md](tracing.md) | `../../tests/behavior/features/tracing.feature` |

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
