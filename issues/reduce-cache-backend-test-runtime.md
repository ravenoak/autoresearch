# Reduce cache backend test runtime

## Context
`tests/unit/test_cache.py::test_cache_is_backend_specific` completes but takes
over 60 seconds and can appear stalled during `task verify`. Its variant
`test_cache_is_backend_specific_without_embeddings` shows similar runtime.
Interrupting either test raises `StorageError: Ontology reasoning interrupted`.

## Dependencies
None

## Acceptance Criteria
- `task verify` completes without manual interruption from this test.
- Runtime of `test_cache_is_backend_specific` is reduced or justified in documentation.
- Warnings from `rdflib_sqlalchemy` are addressed or documented.

## Status
Open
