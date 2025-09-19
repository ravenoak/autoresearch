# Resolve resource tracker errors in verify

## Context
`task verify` previously exited with multiprocessing resource tracker
`KeyError` messages after unit tests, preventing integration tests and
coverage from completing.

Evaluating `./scripts/setup.sh --print-path` now exposes Go Task 3.45.4 in the
base shell, so `task verify` can run without an extra `uv` wrapper once the
venv PATH helper is loaded. 【5d8a01†L1-L2】 The storage selections that
previously crashed now complete: `uv run --extra test pytest tests/unit -k
"storage" -q --maxfail=1` reports 135 passed, 2 skipped, 1 xfailed, and 1 xpassed
tests. 【dbf750†L1-L1】 The next step is to rerun `task verify` directly (ideally
with `PYTHONWARNINGS=error::DeprecationWarning`) to confirm the resource tracker
tear-down path is stable now that the storage guard is fixed. Before that rerun
we must realign the monitor and extensions specs with the lint template
(`restore-spec-lint-template-compliance`) because `uv run python
scripts/lint_specs.py` still fails, blocking the verify workflow until the
headings are restored.【4076c9†L1-L2】【F:issues/restore-spec-lint-template-compliance.md†L1-L33】

## Dependencies
- [restore-spec-lint-template-compliance](restore-spec-lint-template-compliance.md)

## Acceptance Criteria
- `task verify` completes without resource tracker errors.
- Integration tests and coverage reporting run to completion.
- Root cause and mitigation are documented.

## Status
Open
