# Fix flake8 errors in tests

## Context
`task verify` fails flake8 because `tests/unit/test_ui_save_config.py` and
`tests/unit/test_vss_has_vss.py` include unused imports.

## Dependencies
None.

## Acceptance Criteria
- Remove unused imports or apply proper suppression so flake8 reports no F401
  errors in these tests.
- `task verify` completes the flake8 stage without failures.

## Status
Open
