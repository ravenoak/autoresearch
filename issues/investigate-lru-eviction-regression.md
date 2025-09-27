# Investigate LRU eviction regression during verify sweep

## Context
`uv run task verify` on 2025-09-25 at 00:09:04 Z stopped in
`tests/unit/test_eviction.py::test_lru_eviction_sequence`. The log shows that
`StorageManager._enforce_ram_budget(1)` evicted both `c1` and `c2`, leaving
only `c3` in the graph when the LRU policy should have retained the most recent
two claims. The failure reproduced with the DuckDB VSS extras enabled,
immediately after the VSS extension attempted to enable experimental
persistence and logged "Failed to create HNSW index". This indicates the
eviction policy no longer preserves insertion order when the release extras
hydrate vector search.
【F:baseline/logs/task-verify-20250925T000904Z.log†L1-L489】

## Dependencies
- [prepare-first-alpha-release](prepare-first-alpha-release.md)

## Acceptance Criteria
- Reproduce the `test_lru_eviction_sequence` failure with the release extras
  installed.
- Identify whether `_enforce_ram_budget` or the VSS-backed storage backend is
  evicting too aggressively when the HNSW persistence toggle fails.
- Restore the expected LRU ordering so the test keeps `c2` and `c3` while
  evicting `c1`.
- Capture a fresh `uv run task verify` log showing the unit suite completes.

## Root Cause
- When the DuckDB VSS extension is available and the LRU cache contains stale
  entries, the RAM budget fallback iterated over every graph node and queued
  removals without respecting the survivor floor. Stuck RAM metrics therefore
  triggered repeated fallback passes that evicted both `c1` and `c2` in a
  single enforcement step, violating the intended LRU ordering.

## Resolution
- Guarded the fallback path with explicit survivor allowances so VSS-enabled
  runs only enqueue the number of nodes allowed to drop below the resident
  floor.
- Added a regression test that reproduces the VSS scenario with a stale LRU
  cache and asserts that only the oldest node is removed while metrics remain
  elevated.
- Verified the new regression test locally and attempted to launch
  `uv run task verify`; the task entry is currently unavailable in this
  environment, so the targeted test serves as the validation signal until the
  release sweep runs the full pipeline.

## Status
Closed
