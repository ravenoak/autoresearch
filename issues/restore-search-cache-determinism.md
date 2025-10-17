# Restore search cache determinism

## Context
Several cache-focused tests fail under `uv run --extra test pytest`, including
`tests/unit/test_cache.py::test_search_uses_cache`,
`::test_cache_is_backend_specific`, and the stubbed backend scenarios in
`tests/unit/test_core_modules_additional.py`. Cache misses now increment
backend calls unexpectedly and mutate query text.
【7be155†L145-L228】

As of **October 9, 2025 at 16:46 UTC** canonical storage hints keep duckdb
embedding caches and storage-hybrid seeds aligned. The revived
`tests/unit/legacy/test_cache.py::test_interleaved_storage_paths_share_cache`
run proves deterministic hits using unified hint tuples, and `uv run task
check` remains green with the same configuration.【F:src/autoresearch/search/core.py†L877-L1012】【F:src/autoresearch/search/core.py†L2386-L2421】【F:src/autoresearch/search/core.py†L2440-L2450】【F:src/autoresearch/search/core.py†L2633-L2668】【F:src/autoresearch/search/cache.py†L32-L75】【F:baseline/logs/test-cache-interleaved-20251009T164613Z.log†L1-L8】【F:baseline/logs/task-check-20251009T164646Z.log†L1-L43】

As of **October 9, 2025 at 22:49 UTC** `Search.external_lookup` records
namespace-annotated cache traces with fingerprint data, and the cache helpers
emit store, hit, and miss events for Hypothesis diagnostics. The
`test_interleaved_storage_paths_share_cache` property now provisions a unique
TinyDB path per example, asserts the first backend execution, and inspects the
trace before confirming deterministic hits. A focused Hypothesis run and the
`uv run task check` sweep both pass, confirming cache reuse remains stable
during storage interleaving.【F:src/autoresearch/search/core.py†L700-L905】【F:src/autoresearch/search/core.py†L987-L1116】【F:src/autoresearch/search/core.py†L2382-L2400】【F:src/autoresearch/search/core.py†L2899-L3005】【F:tests/unit/legacy/test_cache.py†L898-L1082】【0d7622†L1-L13】【9b81ca†L1-L8】

## Dependencies
- [prepare-first-alpha-release](prepare-first-alpha-release.md)

## Acceptance Criteria
- Cache lookups reuse backend results instead of reissuing duplicate fetches.
- Backend selection honours context-aware flags and preserves the original query
  string.
- All cache-related unit tests pass without monkeypatch workarounds.
- Telemetry or documentation explains the restored cache semantics.
- Cache keys include backend identity, normalized queries, and embedding flags.
- Fallback placeholders expose deterministic URLs under the `__fallback__`
  namespace.

## Status
**✅ READY FOR v0.1.0** - Search cache determinism restored and tested
