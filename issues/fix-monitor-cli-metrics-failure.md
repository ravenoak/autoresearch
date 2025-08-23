# Fix monitor CLI metrics failure

## Context
`task check` reports `tests/unit/test_monitor_cli.py::test_monitor_metrics` failing,
asserting `130 == 0`. This indicates the monitor CLI is not producing the expected
metrics and needs investigation.

## Acceptance Criteria
- Identify the root cause of the metrics mismatch.
- Fix the monitor CLI or test to ensure expected metrics.
- Update documentation if monitor behavior changes.

## Status
Open
