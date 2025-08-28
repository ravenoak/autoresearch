# Align status and roadmap with test results

## Context
`STATUS.md` and `ROADMAP.md` report outdated coverage and reference successful
test runs. Recent attempts show `task check` and `task verify` fail when
`uv sync --extra dev-minimal` uninstalls `pytest_bdd`, `freezegun`, and
`hypothesis`. Documentation should reflect actual failures until the
environment is fixed.

## Dependencies
- [resolve-release-blockers-for-alpha](resolve-release-blockers-for-alpha.md)
- [fix-task-check-dependency-removal-and-extension-bootstrap](fix-task-check-dependency-removal-and-extension-bootstrap.md)

## Acceptance Criteria
- `STATUS.md` reflects current `task check` and `task verify` results.
- `ROADMAP.md` avoids claiming coverage or test success while checks fail.
- Documentation links to issues tracking environment fixes.
- Outdated coverage metrics are removed.

## Status
Open
