# Ensure pytest-bdd plugin is available for tests

## Context
Running `uv run pytest` fails with `ImportError: No module named 'pytest_bdd'`, indicating the plugin is missing from the installed extras. Even targeted tests emit `PytestConfigWarning: Unknown config option: bdd_features_base_dir`, showing the test suite expects `pytest-bdd` to be present.

## Dependencies
None

## Acceptance Criteria
- `pytest-bdd` is included in the test environment or documented as a required extra.
- `uv run pytest` collects tests without an ImportError.
- Targeted tests run without `bdd_features_base_dir` warnings.

## Status
Open
