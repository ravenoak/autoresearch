# Resolve integration test regressions

## Context
Running `uv run --extra test pytest` previously reported a failing
integration test. After fixes, a full run now passes
(`289 passed`, `10 skipped`) though RDFlib/SQLAlchemy deprecation warnings
remain. This resolution unblocks `prepare-first-alpha-release`, while
follow-up warning cleanup is tracked separately.

## Dependencies
- [fix-api-authentication-and-metrics-tests](archive/fix-api-authentication-and-metrics-tests.md)
- [fix-search-ranking-and-extension-tests](archive/fix-search-ranking-and-extension-tests.md)
- [fix-rdf-persistence-and-search-storage-tests](archive/fix-rdf-persistence-and-search-storage-tests.md)
- [fix-storage-schema-and-eviction-tests](archive/fix-storage-schema-and-eviction-tests.md)

## Acceptance Criteria
- API endpoints require keys and return correct status codes.
- Configuration reload tests pass for both atomic and live updates.
- Deployment validation scripts handle success and schema errors.
- Monitoring metrics endpoint responds with HTTP 200.
- VSS extension loader initializes successfully.
- Ranking formula tests match documented values.
- RDF persistence and search storage tests pass with DuckDB backends.
- Storage eviction simulations maintain expected node counts.

## Status
Archived
