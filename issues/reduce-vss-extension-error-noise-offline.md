# Reduce VSS extension error noise when offline

## Context
Running `uv run --extra test pytest tests/unit/test_storage_eviction_sim.py::
test_under_budget_keeps_nodes -q` in the evaluation container emits
repeated error-level logs from DuckDB while the VSS extension loader
falls back to the stub file. The output reports failed HTTP downloads
and missing catalog settings before the stub completes, including
repeated "Failed to create HNSW index" messages, even though the
simulation ultimately proceeds. 【3b2b52†L1-L60】 The noise obscures the
storage regression signal and suggests a fatal failure despite the
existing offline fallback. We should downgrade or consolidate these
messages when the loader falls back to stubbed extensions so offline
test runs remain readable.

## Dependencies
- None

## Acceptance Criteria
- Offline runs of the storage eviction simulation avoid repeated
  error-level log lines about VSS extension downloads when the stub
  fallback engages.
- Logging documents the fallback path at `INFO` or lower while still
  surfacing genuine loader errors.
- STATUS.md or TASK_PROGRESS.md notes the quieter behavior once the
  logging change ships.

## Status
Open
