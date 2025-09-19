# Prepare first alpha release

## Context
The project remains unreleased even though the codebase and documentation are
public. To tag v0.1.0a1 we still need a coordinated push across testing,
documentation, and packaging while keeping workflows dispatch-only. Running
`uv run python scripts/check_env.py` continues to confirm the expected
toolchain once the `dev-minimal` and `test` extras are synced, and sourcing the
PATH helper emitted by `./scripts/setup.sh --print-path` makes `task
--version` report Go Task 3.45.4 immediately. 【0feb5e†L1-L17】【fa650a†L1-L10】【5d8a01†L1-L2】
The storage suite that previously aborted now completes:
`uv run --extra test pytest tests/unit -k "storage" -q --maxfail=1` finishes with
135 passed, 2 skipped, 1 xfailed, and 1 xpassed tests. 【dbf750†L1-L1】 The xpass
comes from `tests/unit/test_storage_errors.py::test_setup_rdf_store_error`, so
the stale xfail marker needs to be removed to keep storage error handling
covered. 【cd543d†L1-L1】 `uv run --extra docs mkdocs build` still succeeds
without navigation warnings, so the docs pipeline is ready once tests pass.
【e808c5†L1-L2】 The release checklist now depends on cleaning up the xpass,
re-running `task verify` to confirm the resource tracker fix, and refreshing
coverage before we can tag 0.1.0a1. The latest `task check` run fails in
`scripts/lint_specs.py` because the monitor and extensions specs drifted from
the required headings, so we opened `restore-spec-lint-template-compliance` to
restore spec lint compliance before rerunning full test and coverage
workflows.【4076c9†L1-L2】【F:issues/restore-spec-lint-template-compliance.md†L1-L33】

## Dependencies
- [resolve-resource-tracker-errors-in-verify](resolve-resource-tracker-errors-in-verify.md)
- [resolve-deprecation-warnings-in-tests](resolve-deprecation-warnings-in-tests.md)
- [rerun-task-coverage-after-storage-fix](rerun-task-coverage-after-storage-fix.md)
- [remove-stale-xfail-for-rdf-store-error](remove-stale-xfail-for-rdf-store-error.md)
- [restore-spec-lint-template-compliance](restore-spec-lint-template-compliance.md)

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
