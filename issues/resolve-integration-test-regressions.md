# Resolve integration test regressions

## Context
Running `uv run --extra test pytest` reports 52 failing integration tests.
Failures span API key enforcement, configuration hot reload, deployment
validation, monitoring metrics, VSS extension loading, ranking
consistency, RDF persistence and search storage. These regressions block
the `prepare-first-alpha-release` issue and are split across dedicated
tickets for targeted fixes.

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
Open
