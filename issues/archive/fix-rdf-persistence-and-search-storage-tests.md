# Fix RDF persistence and search storage tests

## Context
RDF persistence and search storage integration tests fail.
`tests/integration/test_rdf_persistence.py::test_oxigraph_backend_initializes`
raises backend errors, and multiple
`tests/integration/test_search_storage.py` cases cannot persist or retrieve
claims.

## Dependencies
None.

## Acceptance Criteria
- RDF backend initializes with DuckDB and Oxigraph.
- Search storage persists and retrieves multiple backend results.
- Related integration tests pass.
- Documentation links persistence behavior to storage APIs.

## Status
Archived
