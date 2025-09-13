# Reduce cache backend test runtime

## Context
`tests/unit/test_cache.py::test_cache_is_backend_specific` completes but takes
over 60 seconds and can appear stalled during `task verify`. Its variant
`test_cache_is_backend_specific_without_embeddings` shows similar runtime.
Interrupting either test raises `StorageError: Ontology reasoning interrupted`.

On September 13, 2025, the test completed in about 0.22 seconds, but the old
`rdflib_sqlalchemy` plugin still emitted deprecation warnings. The project now
uses `oxrdflib` to avoid these warnings.

On the latest run on September 13, 2025, `task verify` reported
`test_cache_is_backend_specific` completing in roughly 0.26 seconds and its
variant finishing in about 0.21 seconds. Performance is now acceptable and the
switch to `oxrdflib` eliminated previous deprecation warnings.

## Dependencies
None

## Acceptance Criteria
- `task verify` completes without manual interruption from this test.
- Runtime of `test_cache_is_backend_specific` is reduced or justified in documentation.
 - Warnings from the former `rdflib_sqlalchemy` plugin are eliminated or documented.

## Status
Open
