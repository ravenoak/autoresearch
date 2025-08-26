# Prepare first alpha release

## Context
Version 0.1.0a1 will be the project's first public alpha. Running
`scripts/setup.sh` now installs Go Task alongside development and test extras,
allowing checks to run via `./.venv/bin/task`. `flake8` and `mypy` succeed, yet
`./.venv/bin/task check` still reports numerous failures. Unit tests surface
`StorageError: Failed to initialize schema version` and CLI help regressions,
while integration and behavior suites abort early. Coverage remains at **67%**
and TestPyPI uploads continue to fail with HTTP 403. Release notes and
packaging instructions are still incomplete.

## Milestone

- 0.1.0a1 (2026-04-15)

## Dependencies

- [document-environment-bootstrap](
  archive/document-environment-bootstrap.md)
- [verify-packaging-workflow-and-duckdb-fallback](
  archive/verify-packaging-workflow-and-duckdb-fallback.md)
- [stabilize-integration-tests](
  archive/stabilize-integration-tests.md)
- [add-coverage-gates-and-regression-checks](
  archive/add-coverage-gates-and-regression-checks.md)
- [validate-ranking-algorithms-and-agent-coordination](
  archive/validate-ranking-algorithms-and-agent-coordination.md)

## Acceptance Criteria
- `task check` and `task verify` complete on a fresh clone without
  hanging during `mypy`.
- Unit tests install required extras (`pytest_httpx`, `tomli_w`) and pass
  consistently.
- Integration tests run with `redis` available or skip cleanly when absent.
- Behavior suite passes or scenarios are updated.
- Coverage meets the **90%** threshold.
- TestPyPI upload succeeds without authorization errors.
- Release notes and packaging instructions drafted.
- Backlog prioritized for post-alpha milestones.

## Status
Open

