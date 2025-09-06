# Resolve resource tracker errors in verify

## Context
`task verify` previously exited with multiprocessing resource tracker `KeyError`
messages after unit tests, preventing integration tests and coverage from
completing.

On September 6, 2025, running `task verify` aborted on unrelated test failures
before reaching integration tests (first
`tests/unit/test_metrics_token_budget_spec.py::test_token_budget_spec` and
`tests/unit/test_token_budget.py::test_token_budget`, later
`tests/integration/test_optional_modules_imports.py::test_optional_module_exports[spacy-__version__]`),
so no resource tracker errors were reproduced. Auditing fixtures that spawn
multiprocessing pools and queues showed they call `close()` and
`join_thread()`, leaving no unclosed resources.

Given the failure stemmed from unrelated test errors, no regression test was
added.

## Dependencies
- None

## Acceptance Criteria
- `task verify` completes without resource tracker errors.
- Integration tests and coverage reporting run to completion.
- Root cause and mitigation are documented.

## Status
Archived
