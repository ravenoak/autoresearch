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
Open
