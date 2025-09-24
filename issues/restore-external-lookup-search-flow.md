# Restore external lookup search flow

## Context
`tests/unit/test_search.py::test_external_lookup_vector_search` and
`tests/unit/test_search.py::test_external_lookup_hybrid_query` remain
marked with `xfail` and still report as XFAIL after the September 24 run
of `uv run --extra test pytest tests/unit -m "not slow" -rxX`. The
markers document two gaps: the search module does not expose the
configured `StorageManager`, and the hybrid lookup path still treats the
embedding backend as a placeholder. Documentation in
`docs/algorithms/search.md` and `docs/algorithms/cache.md` claims that
external lookups hydrate semantic caches before ranking, yet the tests
prove the integration is incomplete.

A dialectical review needs to decide whether the hybrid lookup should be
delivered as part of 0.1.0a1 or deferred with explicit documentation.
Socratic questioning of the assumptions—particularly the expectation
that storage-backed lookups are optional—will guide the implementation
work so that the alpha release matches the advertised behavior.

## Dependencies
- _None_

## Acceptance Criteria
- Surface a `StorageManager` handle (or an equivalent cache abstraction)
  through `src/autoresearch/search/__init__.py` so external lookup flows
  can persist and retrieve nodes without private imports.
- Implement the hybrid external lookup path with deterministic behavior
  across BM25, semantic, and ontology stores, updating
  `src/autoresearch/search/core.py` as needed.
- Remove the `xfail` markers from the affected tests and ensure they pass
  consistently under `uv run --extra test pytest tests/unit -m "not slow"
  -rxX`.
- Update `docs/algorithms/search.md` and `docs/algorithms/cache.md` to
  describe the hydrated external lookup sequence, including any fallback
  strategies.
- Map the refreshed behavior in `SPEC_COVERAGE.md` and record the change
  in `CHANGELOG.md` under the Unreleased section.

## Status
Open
