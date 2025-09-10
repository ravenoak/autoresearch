# Fix API authentication integration tests

## Context
Running `uv run --extra test pytest` on September 9, 2025 reports 33
failing tests, the majority of which target authentication and
documentation endpoints. Suites affected include
`tests/integration/test_api_auth.py`, `test_api_auth_middleware.py`,
`test_api_auth_permissions.py`, `test_api_docs.py`, `test_api_additional.py`,
`test_api_streaming.py`, `test_cli_http.py`, and
`test_monitor_metrics.py`. Related failures also surface in
`tests/integration/test_rdf_persistence.py::test_sqlalchemy_backend_initializes`.

## Dependencies
- None

## Acceptance Criteria
- All tests in `tests/integration/test_api_auth*.py` pass.
- `tests/integration/test_api_auth_middleware.py` passes.
- `tests/integration/test_api_auth_permissions.py` passes.
- `tests/integration/test_api_docs.py` passes.
- `tests/integration/test_api_streaming.py` passes.
- `tests/integration/test_cli_http.py::test_http_api_key` passes.
- `tests/integration/test_monitor_metrics.py::test_system_monitor_metrics_exposed` passes.
- `tests/integration/test_optional_extras.py::test_inmemory_broker_roundtrip` passes.
- `tests/integration/test_rdf_persistence.py::test_sqlalchemy_backend_initializes` passes.
- `tests/integration/test_validate_deploy.py` passes.

## Status
Archived
