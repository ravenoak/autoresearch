# Resolve current test failures

## Context
Recent test runs with `uv run pytest -q` still fail. After installing
missing development dependencies and updating several ranking tests, the
suite now exits with numerous failures across unit and integration tests,
including `tests/unit/test_algorithm_docs.py::test_core_docstrings_reference_docs`
and multiple API and orchestrator integration tests. Coverage remains far
below the required threshold and many endpoints return unexpected 403
responses. The project cannot reach the planned **0.1.0** release until
the suite is green and coverage meets expectations.

On 2025-08-19, `uv run pytest -q` reported dozens of failures with only a
subset of tests executed successfully. Coverage output indicated roughly
19% overall coverage, failing the 90% requirement.

## Acceptance Criteria
- All tests pass with `uv run pytest -q`.
- `uv run pytest --cov=src` reports at least 90% coverage.
- The suite runs without unexpected warnings.

## Status
Open

