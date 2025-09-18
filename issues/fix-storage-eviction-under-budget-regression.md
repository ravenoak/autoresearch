# Fix storage eviction under-budget regression

## Context
Running `uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1`
now fails at `tests/unit/test_storage_eviction_sim.py::
test_under_budget_keeps_nodes`. The scenario sets
`StorageManager._current_ram_mb` to return `0` so the workload stays
below the `1` MB budget, yet `_enforce_ram_budget` still prunes nodes
until only one remains. 【3b2b52†L1-L60】 The regression stems from
the fallback that derives a deterministic node limit from the RAM budget.
With the default configuration the helper returns `budget_mb`, so the
loop removes entries whenever the graph holds more than one node even
though RAM usage is reported within bounds.
【F:src/autoresearch/storage.py†L520-L578】

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
Open
