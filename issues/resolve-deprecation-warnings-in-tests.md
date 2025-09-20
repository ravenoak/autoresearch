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

## Latest failure signatures (2025-09-20)

- **Storage – RAM eviction regression:**
  `tests/unit/test_eviction.py::test_ram_eviction` now leaves both `c1` and
  `c2` nodes in the in-memory graph, so the eviction assertion fails. The log
  shows DuckDB VSS emitting
  `Failed to create HNSW index: Catalog Error: Setting with name
  "hnsw_enable_experimental_persistence" is not in the catalog`, suggesting the
  storage backend never prunes the first claim. Assign follow-up to the storage
  maintainers to restore the eviction behavior under warnings-as-errors.

## Dependencies
- [resolve-resource-tracker-errors-in-verify](resolve-resource-tracker-errors-in-verify.md)
- [remove-stale-xfail-for-rdf-store-error](remove-stale-xfail-for-rdf-store-error.md)
- [restore-spec-lint-template-compliance](restore-spec-lint-template-compliance.md)

## Acceptance Criteria
- Unit and integration tests run without deprecation warnings, including a
  `task verify` run with `PYTHONWARNINGS=error::DeprecationWarning`.
- Deprecated APIs are replaced or dependencies pinned to supported versions.
- Documentation notes any unavoidable warnings.

## Multi-PR Remediation Plan

### PR 1 – Establish warnings-as-errors harness and baseline log
- Add a dedicated Taskfile target (e.g., `task verify:warnings`) that wraps
  `PYTHONWARNINGS=error::DeprecationWarning uv run task verify` so future PRs
  can invoke a single command instead of remembering the environment flag.
- Provision a clean virtual environment (`uv sync --frozen --all-extras` for
  reproducibility), document the exact steps in the Task description, and run
  the new task to capture the first failure log.
- Archive the raw command output under `baseline/logs/` with a timestamped file
  name and add a README snippet describing how to regenerate the log.
- Summarize the failure modes in this issue and open follow-up TODO checklists
  that map each deprecation to the owning package or module so the next PRs
  have concrete targets.

### PR 2 – Refactor in-repo callers of deprecated APIs
- For each warning traced to modules under `src/` or `tests/`, replace the
  deprecated API usage with the forward-compatible alternative (e.g., migrate
  helper shims to their permanent home or adopt new keyword arguments).
- Update or extend tests to cover the new code paths and guard against regressions.
- Keep commits focused per module when practical so the dependency updates in
  PR 3 stay isolated.
- Re-run `task verify:warnings`; attach the refreshed log to the baseline folder
  and note the resolved warnings in this issue.

### PR 3 – Align dependencies or add scoped filters
- For remaining warnings triggered by third-party libraries, decide between a
  version bump and a pin to the last safe release; update `pyproject.toml`
  accordingly and regenerate `uv.lock` with `uv lock` so CI enforces the
  constraint.
- When an upstream fix is unavailable, add a targeted filter (e.g., in
  `sitecustomize.py`) explaining the upstream ticket and why suppression is
  temporary. Avoid global filters that could mask new regressions.
- Document the dependency and filter decisions in `CHANGELOG.md` or relevant
  issue notes so the rationale is easy to audit later.
- Run `task verify:warnings` one final time, ensure the log is clean, and store
  the passing log snapshot beside the earlier failures for provenance.

## Status
Open
