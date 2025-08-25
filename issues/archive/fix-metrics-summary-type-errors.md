# Fix metrics summary type errors

## Context
Unit tests `tests/unit/test_metrics_extra.py::test_cycle_and_agent_metrics` and
`tests/unit/test_metrics_summary.py::test_metrics_summary` raise `TypeError:
'types.SimpleNamespace' object is not callable`, indicating the metrics
utilities return incorrect types.

## Acceptance Criteria
- Metrics helpers return callable objects and no longer raise `TypeError`.
- `tests/unit/test_metrics_extra.py::test_cycle_and_agent_metrics` passes.
- `tests/unit/test_metrics_summary.py::test_metrics_summary` passes.
- Documentation clarifies expected metrics interfaces.

## Status
Archived
