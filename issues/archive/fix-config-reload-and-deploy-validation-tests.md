# Fix config reload and deploy validation tests

## Context
Configuration reload and deployment validation tests fail.
`tests/integration/test_config_hot_reload_components.py::test_config_hot_reload_components`,
`tests/integration/test_config_reload.py::test_atomic_swap_and_invalid_config`,
`tests/integration/test_config_reload.py::test_live_reload_without_restart`,
`tests/integration/test_deploy_validation.py::test_validate_deploy_success`, and
`tests/integration/test_deploy_validation.py::test_validate_deploy_env_schema_error`
report incorrect reload behavior and schema handling.

## Dependencies
None.

## Acceptance Criteria
- Configuration hot reload works for component swaps and invalid config paths.
- Deployment validation scripts handle success and schema errors.
- Relevant integration tests pass.
- Updated docs describe reload and validation workflows.

## Status
Archived
