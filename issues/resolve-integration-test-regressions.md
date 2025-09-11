# Resolve integration test regressions

## Context
Running `uv run --extra test pytest` reports 52 failing integration tests. Failures span API key enforcement, configuration hot reload, deployment validation, monitoring metrics, VSS extension loading, ranking consistency, RDF persistence, and search storage. These regressions block the `prepare-first-alpha-release` issue.

## Dependencies
None.

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
