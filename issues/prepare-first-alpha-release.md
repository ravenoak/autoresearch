# Prepare first alpha release

## Context
Version 0.1.0a1 will be the project's first public alpha. A fresh clone on
**August 24, 2025** lacked the Go Task binary and dev extras such as
`tomli_w`, `freezegun`, and `hypothesis`, so `task check` and `task verify`
could not run. After manually installing `pytest-httpx` and `pytest-bdd`, unit
tests still aborted during collection with `ModuleNotFoundError: tomli_w`, and
`uv run pytest tests/behavior/features/api_orchestrator_integration.feature -q`
reported "no match in any of [<Dir features>]". Integration tests execute with
`redis` installed, but coverage remains at **24%**, far below the **90%**
target. The TestPyPI upload returns HTTP 403, and release notes and packaging
steps are incomplete.

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

