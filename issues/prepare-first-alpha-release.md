# Prepare first alpha release

## Context
Version 0.1.0a1 will be the project's first public alpha. The environment
provisions via `scripts/setup.sh`, yet `task check` stalls during unit tests
and `task verify` hangs during `mypy`. Integration tests require the
`redis` package, behavior tests remain unreliable, and several unit tests
need additional dependencies such as `pytest_httpx` and `tomli_w`.
Coverage sits at **24%**, far below the **90%** target, and the TestPyPI
upload currently returns HTTP 403. Release notes and packaging steps are
incomplete.

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

