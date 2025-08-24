# Fix monitor CLI metrics failure

## Context
`task check` and `task verify` report failures in
`tests/unit/test_monitor_cli.py::test_monitor_metrics` and
`::test_monitor_prompts_and_passes_callbacks`, each asserting `130 == 0`.
The monitor CLI is not producing the expected metrics and needs investigation.

## Acceptance Criteria
- Identify the root cause of the metrics mismatch.
- Fix the monitor CLI or test to ensure expected metrics.
- Update documentation if monitor behavior changes.

## Status
Archived

