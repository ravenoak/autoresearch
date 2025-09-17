# Resolve resource tracker errors in verify

## Context
`task verify` previously exited with multiprocessing resource tracker
`KeyError` messages after unit tests, preventing integration tests and
coverage from completing.

On September 17, 2025, the environment still lacks the Go Task CLI by default,
so a fresh `task verify` run has not been attempted. `task --version` continues
to report "command not found", and after resyncing the `dev-minimal`, `test`,
and `docs` extras, `uv run python scripts/check_env.py` confirms that Go Task
is the remaining prerequisite. 【6c3849†L1-L3】【e6706c†L1-L26】 Targeted retries
of the distributed coordination property suite and the VSS extension loader
tests complete without resource tracker errors, suggesting the cleanup helpers
remain effective once the suite reaches teardown. 【d3124a†L1-L2】【669da8†L1-L2】
The storage teardown regression has been fixed—the patched
`ConfigLoader.load_config` scenario now passes—so the unit suite progresses to
the storage eviction simulation. 【04f707†L1-L3】 `uv run --extra test pytest
tests/unit -k "storage" -q --maxfail=1` now fails at
`tests/unit/test_storage_eviction_sim.py::test_under_budget_keeps_nodes`
because `_enforce_ram_budget` trims nodes even when usage stays within the
budget. 【d7c968†L1-L164】 Until the eviction regression and Go Task gap are
resolved we still cannot exercise `task verify` end-to-end to confirm the
resource tracker fix.

## Dependencies
- [fix-storage-eviction-under-budget-regression](
  fix-storage-eviction-under-budget-regression.md)

## Acceptance Criteria
- `task verify` completes without resource tracker errors.
- Integration tests and coverage reporting run to completion.
- Root cause and mitigation are documented.

## Status
Open
