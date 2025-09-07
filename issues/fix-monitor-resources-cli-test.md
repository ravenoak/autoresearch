# Fix monitor resources CLI test

## Context
`tests/integration/test_monitor_metrics.py::test_monitor_resources_cli` fails with `assert 130 == 0`,
indicating the CLI reports unexpected resource counts.

## Dependencies
- None

## Acceptance Criteria
- `tests/integration/test_monitor_metrics.py::test_monitor_resources_cli` passes.

## Status
Open
