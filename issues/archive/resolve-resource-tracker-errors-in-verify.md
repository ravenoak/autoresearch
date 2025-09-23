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

Dropping the fallback `sys` import in
`tests/targeted/test_extras_codepaths.py` cleared the last `flake8` failure so
`task verify` could progress into the test phases needed to exercise the
resource tracker shutdown path. 【F:tests/targeted/test_extras_codepaths.py†L9-L22】
Running `task verify` with `PYTHONWARNINGS=error::DeprecationWarning` against
the baseline extras then completed unit, integration, and behavior suites plus
coverage without surfacing resource tracker `KeyError` messages.
【a74637†L1-L3】【F:baseline/logs/task-verify-20250923T204732Z.log†L2-L6】

## Dependencies

- [clean-up-flake8-regressions-in-routing-and-search-storage](../clean-up-flake8-regressions-in-routing-and-search-storage.md)

## Acceptance Criteria
- `task verify` completes without resource tracker errors.
- Integration tests and coverage reporting run to completion.
- Root cause and mitigation are documented.

## Status
Archived – `task verify` now runs end-to-end with warnings treated as errors and
no resource tracker regressions.

## Resolution
- `task verify` with `dev-minimal` and `test` extras reported 890 passed unit
  tests before continuing into integration and behavior coverage.
  【F:baseline/logs/task-verify-20250923T204732Z.log†L2-L6】
  【F:baseline/logs/task-verify-20250923T204732Z.log†L1046-L1046】
- Integration runs added 324 more passing tests, and behavior checks finished
  with 29 passes while maintaining full coverage reports.
  【F:baseline/logs/task-verify-20250923T204732Z.log†L1441-L1441】
  【F:baseline/logs/task-verify-20250923T204732Z.log†L1748-L1785】
- Searching the verify log for "resource tracker" returned no matches,
  confirming the teardown cache cleanup held. 【128a65†L1-L2】
