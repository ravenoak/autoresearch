# Resolve deprecation warnings in tests

## Context

Recent test runs emitted deprecation warnings from packages such as Click and
fastembed. The `weasel.util.config` module used to trigger a warning because it
imported `click.parser.split_arg_string`, which will move in Click 9.0. These
warnings may become errors in future releases and obscure test output.

`rdflib_sqlalchemy` warnings were eliminated on September 13, 2025 by switching
to `oxrdflib`.

On September 23, 2025 the warnings-as-errors sweep still cannot complete
because `task check` halts in `flake8` after sourcing
`./scripts/setup.sh --print-path`: `src/autoresearch/api/routing.py` assigns an
unused `e` variable and `src/autoresearch/search/storage.py` imports
`StorageError` without using it, so the suite fails before reaching
`PYTHONWARNINGS=error::DeprecationWarning`.【153af2†L1-L2】【1dc5f5†L1-L24】【d726d5†L1-L3】
`uv run python scripts/check_env.py` still reports the expected toolchain once
the `dev-minimal` and `test` extras are synced, and the storage selections that
previously aborted now succeed: `uv run --extra test pytest tests/unit -k
"storage" -q --maxfail=1` finishes with 136 passed, 2 skipped, 1 xfailed, and
822 deselected tests, while `tests/unit/test_storage_errors.py::
test_setup_rdf_store_error -q` passes without an xpass. 【0feb5e†L1-L17】【fa650a†L1-L10】【f6d3fb†L1-L2】【fba3a6†L1-L2】
Spec lint is stable—`uv run python scripts/lint_specs.py` succeeds and the
monitor plus extensions specs retain the required `## Simulation
Expectations` heading—so restoring the warnings harness hinges on fixing the
flake8 regressions and validating the resource tracker tear-down path.
【b7abba†L1-L1】【F:docs/specs/monitor.md†L126-L165】【F:docs/specs/extensions.md†L1-L69】
Without the `[test]` extras Pytest still emits
`PytestConfigWarning: Unknown config option: bdd_features_base_dir` during the
storage simulations, so ensuring the extras are installed remains part of the
cleanup. `StorageManager._enforce_ram_budget` still skips deterministic node
caps when the RAM helper reports 0 MB and no override is configured, so
`tests/unit/test_storage_eviction_sim.py::test_under_budget_keeps_nodes` passes
again. 【F:src/autoresearch/storage.py†L596-L606】【c1571c†L1-L2】

## Latest failure signatures (2025-09-20)

- **HTTPX raw body warnings:** `tests/integration/test_api_auth_middleware.py` used
  `data="not json"` to send invalid JSON, triggering `DeprecationWarning: Use
  'content=<...>' to upload raw bytes/text content.` in HTTPX 0.28.1.
  Mitigation: migrate the tests to `content=` and pin HTTPX to `<0.29` until the
  upstream removal lands.

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
- [clean-up-flake8-regressions-in-routing-and-search-storage](clean-up-flake8-regressions-in-routing-and-search-storage.md)

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
