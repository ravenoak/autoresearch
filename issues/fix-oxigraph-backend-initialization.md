# Fix OxiGraph backend initialization

## Context
`uv run pytest` on 2025-09-14 failed in
`tests/integration/test_rdf_persistence.py::test_oxigraph_backend_initializes`.
The backend returned `"Memory"` instead of `"OxiGraph"`, indicating the
OxiGraph storage backend was not configured or imported correctly.

## Dependencies
None

## Acceptance Criteria
- OxiGraph backend initializes and reports the expected identifier.
- Related RDF persistence tests pass.
- Documentation covers enabling OxiGraph in environments and tests.

## Status
Open
