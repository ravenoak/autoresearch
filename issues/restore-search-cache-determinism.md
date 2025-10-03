# Restore search cache determinism

## Context
Several cache-focused tests fail under `uv run --extra test pytest`, including
`tests/unit/test_cache.py::test_search_uses_cache`,
`::test_cache_is_backend_specific`, and the stubbed backend scenarios in
`tests/unit/test_core_modules_additional.py`. Cache misses now increment
backend calls unexpectedly and mutate query text.
【7be155†L145-L228】

## Dependencies
- [prepare-first-alpha-release](prepare-first-alpha-release.md)

## Acceptance Criteria
- Cache lookups reuse backend results instead of reissuing duplicate fetches.
- Backend selection honours context-aware flags and preserves the original query
  string.
- All cache-related unit tests pass without monkeypatch workarounds.
- Telemetry or documentation explains the restored cache semantics.

## Status
Open
