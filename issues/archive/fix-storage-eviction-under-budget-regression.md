# Fix storage eviction under-budget regression

## Context
Running `uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1`
initially failed at `tests/unit/test_storage_eviction_sim.py::
test_under_budget_keeps_nodes`. The scenario sets
`StorageManager._current_ram_mb` to return `0` so the workload stays
below the `1` MB budget, yet `_enforce_ram_budget` still prunes nodes
until only one remains. The regression stemmed from the deterministic
node limit fallback derived from the RAM budget; with the default
configuration the helper returned `budget_mb`, so the loop removed
entries whenever the graph held more than one node even though RAM usage
was reported within bounds. 【F:src/autoresearch/storage.py†L520-L578】

Targeted retries now confirm the regression is fixed:
`uv run --extra test pytest tests/unit/test_storage_eviction_sim.py -q`
passes and `STATUS.md` plus `TASK_PROGRESS.md` record the healthy run.
【3c1010†L1-L2】【F:STATUS.md†L4-L19】【F:TASK_PROGRESS.md†L3-L22】

## Dependencies
- None

## Acceptance Criteria
- `_enforce_ram_budget` keeps all nodes when `_current_ram_mb()` reports
  usage at or below the configured budget.
- `uv run --extra test pytest tests/unit/test_storage_eviction_sim.py::
  test_under_budget_keeps_nodes -q` passes in a fresh environment with
  the `[test]` extras installed.
- Documentation such as `STATUS.md` or `docs/algorithms/storage_eviction.md`
  records the fix and clarifies when deterministic node budgets apply.

## Status
Archived
