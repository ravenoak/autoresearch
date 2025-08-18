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

## Related tests

- [search_cli.feature](../../tests/behavior/features/search_cli.feature)
- [hybrid_search.feature](../../tests/behavior/features/hybrid_search.feature)
- [storage_search_integration.feature](../../tests/behavior/features/storage_search_integration.feature)
- [local_sources.feature](../../tests/behavior/features/local_sources.feature)
- [vector_search_performance.feature](../../tests/behavior/features/vector_search_performance.feature)

## Extending

Add new behaviours with accompanying feature files and reference them
under **Related tests**.
