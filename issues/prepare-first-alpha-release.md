# Prepare first alpha release

## Context

The project remains unreleased even though the codebase and documentation are
public. Tagging v0.1.0a1 still requires a coordinated push across testing,
documentation, and packaging while workflows stay dispatch-only. In the current
Codex shell the Go Task CLI is not on `PATH` until
`./scripts/setup.sh --print-path` is sourced, so we validated linting and type
checks directly with `uv`. 【2d7183†L1-L3】 `uv run --extra dev-minimal --extra
test flake8 src tests` and `uv run --extra dev-minimal --extra test mypy src`
both succeed, confirming the earlier lint regressions remain resolved.
【dab3a6†L1-L1】【240ff7†L1-L1】【3fa75b†L1-L1】【8434e0†L1-L2】 The unit suite now
passes under `uv run --extra test pytest tests/unit -m 'not slow' --maxfail=1
-rxX`, but six tests marked `xfail` report XPASS and require promotion to
ordinary assertions before release. 【8e97b0†L1-L1】【ba4d58†L1-L104】 Integration
and behavior suites complete with skips only for optional extras.
【ab24ed†L1-L1】【187f22†L1-L9】【87aa99†L1-L1】【88b85b†L1-L2】 `uv run --extra docs
mkdocs build` now finishes without warnings after prior documentation fixes, and
all GitHub Actions workflows remain `workflow_dispatch` only.
【6618c7†L1-L4】【69c7fe†L1-L3】【896928†L1-L4】【F:.github/workflows/ci.yml†L1-L22】
`SPEC_COVERAGE.md` continues to map each module to specifications plus proofs,
simulations, or tests, so every component still aligns with the project's
spec-first mandate ahead of the release. 【F:SPEC_COVERAGE.md†L1-L125】 The
remaining work focuses on retiring the stale `xfail` markers, capturing
warnings-as-errors baselines with optional extras, and staging the packaging
artifacts before drafting release notes and tagging v0.1.0a1.

### PR-sized tasks

- **Retire stale xfail markers** – Promote the six XPASS cases in the unit
  suite so release verification runs fail fast when regressions reappear.
  ([retire-stale-xfail-markers-in-unit-suite](retire-stale-xfail-markers-in-unit-suite.md))
- **Refresh warnings-as-errors coverage** – Capture a new
  `PYTHONWARNINGS=error::DeprecationWarning` run with all optional extras to
  ensure the resource tracker cleanup, DuckDB extension fallback, and
  distributed paths stay quiet. (Reuses archived playbooks in
  [`issues/archive/resolve-resource-tracker-errors-in-verify.md`](archive/resolve-resource-tracker-errors-in-verify.md)
  and [`issues/archive/resolve-deprecation-warnings-in-tests.md`](archive/resolve-deprecation-warnings-in-tests.md).)
- **Stage release artifacts** – Draft CHANGELOG.md notes, confirm packaging
  metadata, and plan the `v0.1.0a1` tag once verification runs and documentation
  updates land.

## Dependencies

- [retire-stale-xfail-markers-in-unit-suite](retire-stale-xfail-markers-in-unit-suite.md)

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
