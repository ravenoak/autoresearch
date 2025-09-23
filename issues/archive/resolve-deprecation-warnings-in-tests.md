# Resolve deprecation warnings in tests

## Context

Recent test runs emitted deprecation warnings from packages such as Click and
fastembed. Earlier work replaced the noisy imports under
`weasel.util.config` and refreshed dependency pins, but the suite continued to
rely on a repository-wide `pkg_resources` filter inside `sitecustomize.py`,
masking any regressions during `task verify:warnings` sweeps.
【F:sitecustomize.py†L1-L37】

The final remediation dropped that blanket suppression and reran
`task verify:warnings:log`, producing
`baseline/logs/verify-warnings-20250923T224648Z.log`. The archive shows the unit
(890 passed), integration (324 passed), and behavior (29 passed) suites
completing with warnings promoted to errors, confirming the harness now runs
cleanly. 【F:baseline/logs/verify-warnings-20250923T224648Z.log†L1047-L1047】
【F:baseline/logs/verify-warnings-20250923T224648Z.log†L1442-L1442】
【F:baseline/logs/verify-warnings-20250923T224648Z.log†L1749-L1749】

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

These signatures remain in the historical logs but no longer reproduce after
the targeted API migrations and the `sitecustomize.py` cleanup above.

## Resolution

- Removed the global `warnings.filterwarnings` block from `sitecustomize.py` so
  DeprecationWarnings surface during test runs. 【F:sitecustomize.py†L1-L37】
- Re-ran `task verify:warnings:log`; the archived output shows the full suite
  finishing without DeprecationWarnings or harness failures, and the log is now
  stored at `baseline/logs/verify-warnings-20250923T224648Z.log` for reference.
  【F:baseline/logs/verify-warnings-20250923T224648Z.log†L1047-L1047】
  【F:baseline/logs/verify-warnings-20250923T224648Z.log†L1442-L1442】
  【F:baseline/logs/verify-warnings-20250923T224648Z.log†L1749-L1749】

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
Archived – `task verify:warnings` now completes without DeprecationWarning
noise after removing the repository-wide filter and refreshing the baseline log.
