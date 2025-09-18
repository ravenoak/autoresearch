# Prepare first alpha release

## Context
The project remains unreleased even though the codebase and documentation are
public. To tag v0.1.0a1 we still need a coordinated push across testing,
documentation, and packaging while keeping workflows dispatch-only. As of
2025-09-18 the Go Task CLI is still absent in a fresh environment, so running
`uv run task check` fails until contributors install Task manually. `task
--version` continues to return "command not found", and running `uv run python
scripts/check_env.py` now flags the Go Task CLI plus unsynced development and
test tooling (e.g., `black`, `flake8`, `fakeredis`, `hypothesis`) until `task
install` or `uv sync` installs the extras.
【74a609†L1-L2】【cd57a1†L1-L24】 Targeted test suites confirm that distributed
coordination properties and VSS extension scenarios still pass with the `[test]`
extras installed, but without those extras Hypothesis is missing and the
coordination suite errors during collection.
【791df7†L1-L18】【d3124a†L1-L2】【669da8†L1-L2】 The storage teardown
regression that blocked the monitor metrics suite has been resolved; the patched
scenario now passes. 【04f707†L1-L3】 The unit run now halts at
`tests/unit/test_storage_eviction_sim.py::test_under_budget_keeps_nodes`
because `_enforce_ram_budget` evicts nodes even when the mocked RAM usage stays
within the budget, preventing coverage and release rehearsals from finishing.
【d7c968†L1-L164】 Adding the task coverage log to `mkdocs.yml` cleared the
documentation warning; `uv run --extra docs mkdocs build` still completes
without navigation errors. 【781a25†L1-L1】【a05d60†L1-L2】【bc0d4c†L1-L1】 These gaps
block the release checklist and require targeted fixes before we can tag
0.1.0a1.

## Dependencies
- [restore-distributed-coordination-simulation-exports](restore-distributed-coordination-simulation-exports.md)
- [resolve-resource-tracker-errors-in-verify](resolve-resource-tracker-errors-in-verify.md)
- [resolve-deprecation-warnings-in-tests](resolve-deprecation-warnings-in-tests.md)
- [fix-storage-eviction-under-budget-regression](fix-storage-eviction-under-budget-regression.md)
- [rerun-task-coverage-after-storage-fix](rerun-task-coverage-after-storage-fix.md)

## Acceptance Criteria
- All dependency issues are closed.
- Release notes for v0.1.0a1 are drafted in CHANGELOG.md.
- Git tag v0.1.0a1 is created only after tests pass and documentation is
  updated.
- `task docs` (or `uv run --extra docs mkdocs build`) completes after docs
  extras sync.
- Workflows remain manual or dispatch-only.

## Status
Open
