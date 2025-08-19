# Resolve current test failures

## Context
Earlier runs of `uv run pytest -q` failed due to missing development
dependencies and ranking test issues. Multiple API and orchestrator
integration tests errored, and coverage fell far below the required
threshold.

On 2025-08-19, `uv run pytest -q` reported dozens of failures with only a
subset of tests executed successfully. Coverage output indicated roughly
19% overall coverage, failing the 90% requirement. After installing the
`dev-minimal` extras and addressing the ranking tests, `uv run --extra
dev-minimal pytest -q` completes successfully and the suite meets the
90% coverage target enforced by `--cov-fail-under=90`.

## Acceptance Criteria
- All tests pass with `uv run pytest -q`.
- `uv run pytest --cov=src` reports at least 90% coverage.
- The suite runs without unexpected warnings.

## Status
Archived

