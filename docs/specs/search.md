# Search Module Specification

The search package (`src/autoresearch/search/`) handles retrieving
information from local files, storage backends and vector indexes. It
supports keyword, vector and hybrid queries and exposes a CLI entry
point.

## Key behaviors

- Execute search queries via the `autoresearch search` CLI.
- Combine keyword and vector retrieval for hybrid search results.
- Integrate with the storage subsystem, respecting eviction policies.
- Query local directories, document formats and Git repositories.
- Maintain responsive vector search performance.

## Traceability

- Modules
  - [src/autoresearch/search/][m1]
- Tests
  - [tests/behavior/features/hybrid_search.feature][t1]
  - [tests/behavior/features/local_sources.feature][t2]
  - [tests/behavior/features/search_cli.feature][t3]
  - [tests/behavior/features/storage_search_integration.feature][t4]
  - [tests/behavior/features/vector_search_performance.feature][t5]
  - [tests/integration/test_config_hot_reload_components.py][t6]
  - [tests/integration/test_search_storage.py][t7]

[m1]: ../../src/autoresearch/search/
[t1]: ../../tests/behavior/features/hybrid_search.feature
[t2]: ../../tests/behavior/features/local_sources.feature
[t3]: ../../tests/behavior/features/search_cli.feature
[t4]: ../../tests/behavior/features/storage_search_integration.feature
[t5]: ../../tests/behavior/features/vector_search_performance.feature
[t6]: ../../tests/integration/test_config_hot_reload_components.py
[t7]: ../../tests/integration/test_search_storage.py
