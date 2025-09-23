# Resolve resource tracker errors in verify

## Context

`task verify` previously exited with multiprocessing resource tracker
`KeyError` messages after unit tests, preventing integration tests and
coverage from completing.

Sourcing `./scripts/setup.sh --print-path` exposes Go Task 3.45.4 in the base
shell so `task verify` can run without an extra `uv` wrapper once the PATH
helper is loaded. 【153af2†L1-L2】 The storage selection that used to crash now
finishes with 136 passed, 2 skipped, 1 xfailed, and 822 deselected tests, and
the RDF store regression test passes without an xfail marker, so storage no
longer blocks the teardown path. 【f6d3fb†L1-L2】【fba3a6†L1-L2】 Spec lint also
holds: `uv run python scripts/lint_specs.py` succeeds and the monitor plus
extensions specs retain the required `## Simulation Expectations` heading.
【b7abba†L1-L1】【F:docs/specs/monitor.md†L126-L165】【F:docs/specs/extensions.md†L1-L69】
The outstanding blocker is the new `flake8` failure in `task check`, where
`src/autoresearch/api/routing.py` assigns an unused `e` variable and
`src/autoresearch/search/storage.py` imports `StorageError` without using it,
so `task verify` will continue to stop in linting until that cleanup lands.
【1dc5f5†L1-L24】【d726d5†L1-L3】 Re-run `task verify` (ideally with
`PYTHONWARNINGS=error::DeprecationWarning`) after the lint fix to confirm the
resource tracker shutdown path is stable.

## Dependencies

- [clean-up-flake8-regressions-in-routing-and-search-storage](clean-up-flake8-regressions-in-routing-and-search-storage.md)

## Acceptance Criteria
- `task verify` completes without resource tracker errors.
- Integration tests and coverage reporting run to completion.
- Root cause and mitigation are documented.

## Status
Open
