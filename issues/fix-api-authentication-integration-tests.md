# Fix API authentication integration tests

## Context
`uv run pytest` previously reported 32 failures across authentication and
documentation endpoints. After recent fixes, only
`tests/integration/test_api_docs.py::test_query_endpoint` fails with
`"Error: Invalid response format"`.

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
Open
