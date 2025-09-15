# Fix config weight sum validation

## Context
`uv run pytest tests/unit/test_config_validation_errors.py::test_weights_must_sum_to_one -q`
failed on 2025-09-15. The check for invalid ranking weight totals no longer
raises `ConfigError`, so misconfigured installations silently accept weight
vectors that sum above one. This regression blocks `task verify`.

## Dependencies
None

## Acceptance Criteria
- Reproduce and fix the regression in
  `tests/unit/test_config_validation_errors.py::test_weights_must_sum_to_one`.
- Add regression coverage if additional guard paths are involved.
- Update release notes or specs if validation rules changed.

## Status
Open
