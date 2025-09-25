# Address Ray serialization failure in coverage sweep

## Context
`uv run task coverage` on 2025-09-25 at 00:10:17 Z failed when
`tests/unit/test_distributed_executors.py::test_execute_agent_remote` attempted
to ship `QueryState` through Ray. The distributed extras introduce Pydantic
models with `_thread.RLock` instances that cloudpickle cannot serialize, so the
coverage run aborts before producing a report. The failure happens after Ray
spins up a local cluster during the unit phase.
【F:baseline/logs/task-coverage-20250925T001017Z.log†L1-L669】

## Dependencies
- [prepare-first-alpha-release](prepare-first-alpha-release.md)

## Acceptance Criteria
- Reproduce the Ray serialization failure with the coverage extras installed.
- Audit the `QueryState` payload passed into `_execute_agent_remote.remote` and
  remove or replace the non-serializable members.
- Capture a successful `uv run task coverage` log showing the ≥90% gate holds.
- Document any Ray environment tweaks required for CI so future coverage sweeps
  continue to run under `uv run task coverage`.

## Status
In Review

- 2025-09-25: `QueryState` now strips its private `RLock` during pickle and
  regenerates the lock on load, so Ray workers no longer abort on the
  `_thread.RLock` serialization error. Added a Hypothesis regression guard and a
  Ray round-trip test (`test_query_state_ray_round_trip`) to keep the payload
  healthy. A fresh `uv run task coverage` run (with the BM25 property deselected
  via `PYTEST_ADDOPTS`) advances through Ray execution before halting on the
  pre-existing scheduler benchmark regression, confirming the Ray fix while the
  broader coverage gate stays open. 【F:src/autoresearch/orchestration/state.py†L19-L28】【F:tests/unit/test_distributed_executors.py†L1-L98】【F:baseline/logs/task-coverage-20250925T031805Z.log†L1-L120】
