# Resolve deprecation warnings in tests

## Context
Recent test runs emitted deprecation warnings from packages such as Click and
fastembed. The `weasel.util.config` module used to trigger a warning because it
imported `click.parser.split_arg_string`, which will move in Click 9.0. These
warnings may become errors in future releases and obscure test output.

`rdflib_sqlalchemy` warnings were eliminated on September 13, 2025 by switching
to `oxrdflib`.

On September 17, 2025, targeted retries with
`PYTHONWARNINGS=error::DeprecationWarning`
showed no remaining warnings in the CLI helper suite or distributed perf
comparison test. The `sitecustomize.py` shim that rewrites
`weasel.util.config` appears to be working, and the Click bump to 8.2.1 removed
the original warning. After resyncing the `dev-minimal`, `test`, and `docs`
extras, `uv run python scripts/check_env.py` still reports the expected
toolchain, and evaluating `./scripts/setup.sh --print-path` exposes Go Task
3.45.4 so the warnings sweep can run inside `task verify`.
【0feb5e†L1-L17】【fa650a†L1-L10】【5d8a01†L1-L2】 The storage selections that
previously aborted now succeed: `uv run --extra test pytest tests/unit -k
"storage" -q --maxfail=1` finishes with 135 passed, 2 skipped, 1 xfailed, and 1
xpassed tests. 【dbf750†L1-L1】 The lone xpass comes from
`tests/unit/test_storage_errors.py::test_setup_rdf_store_error`, so we still
need to remove the stale xfail to keep coverage honest while the warning sweep
runs. 【cd543d†L1-L1】 Once the xfail cleanup lands and the resource tracker fix
is verified, rerun `task verify` with `PYTHONWARNINGS=error::DeprecationWarning`
to confirm the suite stays quiet. Without the `[test]` extras Pytest still
emits `PytestConfigWarning: Unknown config option: bdd_features_base_dir`
during the storage simulations, so ensuring the extras are installed remains
part of the cleanup. We must also restore spec lint compliance
(`restore-spec-lint-template-compliance`) because the newest `task check` run
stops in `scripts/lint_specs.py`, preventing `task verify` from reaching the
warnings sweep until the monitor and extensions specs adopt the required
headings.【4076c9†L1-L2】【F:issues/restore-spec-lint-template-compliance.md†L1-L33】

## Dependencies
- [resolve-resource-tracker-errors-in-verify](resolve-resource-tracker-errors-in-verify.md)
- [remove-stale-xfail-for-rdf-store-error](remove-stale-xfail-for-rdf-store-error.md)

## Acceptance Criteria
- Unit and integration tests run without deprecation warnings, including a
  `task verify` run with `PYTHONWARNINGS=error::DeprecationWarning`.
- Deprecated APIs are replaced or dependencies pinned to supported versions.
- Documentation notes any unavoidable warnings.

## Status
Open
