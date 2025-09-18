# Reduce VSS extension error noise when offline

## Context
Running `uv run --extra test pytest tests/unit/test_storage_eviction_sim.py::
test_under_budget_keeps_nodes -q` in the evaluation container initially
emitted repeated error-level logs from DuckDB while the VSS extension
loader fell back to the stub file. The output reported failed HTTP
downloads and missing catalog settings before the stub completed,
including repeated "Failed to create HNSW index" messages, even though
the simulation ultimately proceeded. The noise obscured the storage
regression signal and suggested a fatal failure despite the existing
offline fallback.

The loader now deduplicates error messages and logs fallback activity at
`INFO`, while tests assert the quieter behavior. `STATUS.md` documents
the change so offline runs remain readable. 【F:src/autoresearch/extensions.py†L36-L118】【F:tests/unit/test_vss_extension_loader.py†L173-L227】【F:STATUS.md†L12-L19】

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
Archived
