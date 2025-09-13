# Ensure pytest-bdd plugin is available for tests

## Context
Running `uv run pytest` failed with `ImportError: No module named 'pytest_bdd'`,
indicating the plugin was missing from the installed extras. Even targeted tests
emitted `PytestConfigWarning: Unknown config option: bdd_features_base_dir`,
showing the test suite expected `pytest-bdd` to be present. As of 2025-09-13 the
setup script installs the plugin and targeted tests run without the warning.

## Dependencies
None

## Acceptance Criteria
- `pytest-bdd` is included in the test environment or documented as a required extra.
- `uv run pytest` collects tests without an ImportError.
- Targeted tests run without `bdd_features_base_dir` warnings.

## Status
Archived
